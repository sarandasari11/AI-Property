"""
Audio Synthesis & Dynamic Audio Mixing Engine.
Features:
1. Neural Text-To-Speech (TTS) using edge-tts with selectable voices and accents.
2. Scene-by-scene audio alignment: Measures actual voiceover duration and synchronizes slide lengths.
3. Audio ducking & mixing: Combines spoken narration with royalty-free ambient background music.
"""
import asyncio
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from moviepy import AudioFileClip, CompositeAudioClip

from config import (
    AUDIO_DIR,
    TEMP_DIR,
    DEFAULT_TTS_VOICE,
    BG_MUSIC_VOLUME,
    BG_MUSIC_FULL_VOLUME,
)
from core.script_generator import SceneScript

# Curated list of high-fidelity neural voices for real estate videos
AVAILABLE_VOICES: Dict[str, str] = {
    "en-US-ChristopherNeural": "Christopher (US Male - Professional, Confident)",
    "en-US-JennyNeural": "Jenny (US Female - Warm, Clear)",
    "en-US-GuyNeural": "Guy (US Male - Friendly, Energetic)",
    "en-GB-SoniaNeural": "Sonia (UK Female - Sophisticated, Premium)",
    "en-GB-RyanNeural": "Ryan (UK Male - Elegant, Authoritative)",
    "en-IN-NeerjaNeural": "Neerja (India Female - Warm, Expressive)",
    "en-IN-PrabhatNeural": "Prabhat (India Male - Professional, Clear)",
}


async def _async_synthesize(text: str, output_path: str, voice: str = DEFAULT_TTS_VOICE, rate: str = "+0%"):
    """Internal async coroutine to invoke edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)


def synthesize_speech(text: str, output_path: str, voice: str = DEFAULT_TTS_VOICE, rate: str = "+0%") -> str:
    """
    Synchronous wrapper to synthesize text to an MP3 file using edge-tts.
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_async_synthesize(text=text, output_path=str(p), voice=voice, rate=rate))
    return str(p)


def synthesize_scenes_audio(
    scenes: List[SceneScript],
    voice: str = DEFAULT_TTS_VOICE,
    scene_padding: float = 0.6,
    temp_dir: Optional[Path] = None,
) -> List[Tuple[SceneScript, str, float]]:
    """
    Synthesizes narration for each scene and calculates exact measured audio duration.
    
    Args:
        scenes: List of SceneScript objects.
        voice: Chosen neural TTS voice identifier.
        scene_padding: Pause buffer in seconds after speech finishes (prevents abrupt transitions).
        temp_dir: Directory where temporary audio files will be stored.
        
    Returns:
        List of tuples: (updated_scene_script, audio_file_path, total_scene_duration_sec)
    """
    target_dir = temp_dir or (TEMP_DIR / "audio_scenes")
    target_dir.mkdir(parents=True, exist_ok=True)

    synced_scenes: List[Tuple[SceneScript, str, float]] = []

    for idx, scene in enumerate(scenes):
        audio_file = target_dir / f"scene_{idx:02d}_{scene.scene_type}.mp3"
        
        # 1. Synthesize narration
        synthesize_speech(
            text=scene.voiceover_text,
            output_path=str(audio_file),
            voice=voice,
        )

        # 2. Measure actual audio duration using MoviePy AudioFileClip
        audio_clip = AudioFileClip(str(audio_file))
        actual_voice_duration = audio_clip.duration
        audio_clip.close()

        # 3. Synchronize scene duration with speech + visual comfort padding
        total_scene_duration = round(actual_voice_duration + scene_padding, 2)
        
        # Enforce minimum 4.2s for visual readability of photos and overlays
        total_scene_duration = max(4.2, total_scene_duration)

        # Update scene model duration
        scene.estimated_duration = total_scene_duration

        synced_scenes.append((scene, str(audio_file), total_scene_duration))

    return synced_scenes


def mix_master_soundtrack(
    scene_audio_data: List[Tuple[SceneScript, str, float]],
    bg_music_path: Optional[str] = None,
    output_path: Optional[str] = None,
    music_volume: float = BG_MUSIC_VOLUME,
) -> Tuple[str, float]:
    """
    Composites scene voiceovers with background ambient music and ducking.
    
    Args:
        scene_audio_data: List of (SceneScript, audio_path, scene_duration).
        bg_music_path: Path to background music file (defaults to assets/audio/ambient_property.mp3).
        output_path: Where to save the final master soundtrack file.
        music_volume: Ducked background music volume (e.g., 0.12 = 12%).
        
    Returns:
        Tuple: (master_soundtrack_path: str, total_duration_seconds: float)
    """
    out_file = Path(output_path) if output_path else (TEMP_DIR / "master_soundtrack.mp3")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    voice_clips = []
    current_time_offset = 0.0

    # 1. Position each scene voice clip on the timeline
    for scene, audio_path, scene_dur in scene_audio_data:
        v_clip = AudioFileClip(audio_path)
        # Small 0.25s offset from start of slide for natural video pacing
        positioned_clip = v_clip.with_start(current_time_offset + 0.25)
        voice_clips.append(positioned_clip)
        current_time_offset += scene_dur

    total_video_duration = current_time_offset

    # 2. Prepare background music
    active_bg_path = bg_music_path or str(AUDIO_DIR / "ambient_property.mp3")
    all_audio_tracks = []

    if Path(active_bg_path).exists():
        bg_clip = AudioFileClip(active_bg_path)
        
        # Loop or trim background music to match video duration exactly
        if bg_clip.duration < total_video_duration:
            # Need to loop music if video is longer than track
            repeats = int(total_video_duration // bg_clip.duration) + 1
            from moviepy import concatenate_audioclips
            bg_clip = concatenate_audioclips([bg_clip] * repeats)
        
        bg_trimmed = bg_clip.subclipped(0, total_video_duration)
        # Apply ducking (reduce volume so voiceover is crisp and clear)
        bg_ducked = bg_trimmed.with_volume_scaled(music_volume)
        all_audio_tracks.append(bg_ducked)

    # Add all voice clips
    all_audio_tracks.extend(voice_clips)

    # 3. Composite and render master audio
    composite = CompositeAudioClip(all_audio_tracks)
    composite.write_audiofile(
        str(out_file),
        fps=44100,
        nbytes=2,
        logger=None,
    )

    # Cleanup open clips
    composite.close()
    for clip in all_audio_tracks:
        try:
            clip.close()
        except Exception:
            pass

    return str(out_file), total_video_duration
