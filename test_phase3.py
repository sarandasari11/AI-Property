"""
Phase 3 Verification Script
Validates Neural TTS generation, scene-by-scene speech synchronization,
and audio ducking/mixing with background ambient score.
"""
import sys
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from moviepy import AudioFileClip
from core.validator import PropertyInput
from core.script_generator import generate_property_script
from core.voice_synthesizer import (
    AVAILABLE_VOICES,
    synthesize_speech,
    synthesize_scenes_audio,
    mix_master_soundtrack,
)
from config import TEMP_DIR, AUDIO_DIR


def run_phase3_tests():
    print("=" * 60)
    print("PHASE 3 VERIFICATION: AUDIO GENERATION & DYNAMIC MIXING")
    print("=" * 60)

    # 1. Voice list verification
    print("\n[1/4] Checking Available Voices...")
    assert len(AVAILABLE_VOICES) >= 5, "Must support multiple regional/gender voices"
    for voice_id, desc in list(AVAILABLE_VOICES.items())[:3]:
        print(f" -> Voice: {desc} ({voice_id})")

    # 2. Single TTS synthesis test
    print("\n[2/4] Testing Single TTS Speech Synthesis...")
    test_out = TEMP_DIR / "phase3_test_single.mp3"
    result_path = synthesize_speech(
        text="Welcome to this exquisite property tour.",
        output_path=str(test_out),
        voice="en-US-ChristopherNeural"
    )
    assert Path(result_path).exists(), "Output audio file must exist"
    assert Path(result_path).stat().st_size > 1000, "Audio file must not be empty"
    print(f" -> Single speech synthesized: {Path(result_path).stat().st_size} bytes (OK)")

    # 3. Scene-by-Scene Audio Synchronization
    print("\n[3/4] Testing Scene-by-Scene Synchronization...")
    prop = PropertyInput(
        name="The Horizon Residences",
        location="Austin, Texas",
        price="$1,450,000",
        property_type="Luxury Modern Condo",
        features=[
            "Floor-to-Ceiling Windows with Skyline Views",
            "Designer Kitchen with Quartz Waterfall Island",
            "Resort-Style Heated Rooftop Pool",
        ],
        contact_cta="Contact agent at (512) 555-0145",
        image_paths=[f"temp/img_{i}.jpg" for i in range(4)]
    )
    script = generate_property_script(prop)

    synced_scenes = synthesize_scenes_audio(
        scenes=script.scenes,
        voice="en-US-ChristopherNeural",
        scene_padding=0.6,
        temp_dir=TEMP_DIR / "test_scenes_audio"
    )

    assert len(synced_scenes) == len(script.scenes), "All scenes must have audio synthesized"
    total_scene_time = 0.0
    for idx, (sc, audio_path, dur) in enumerate(synced_scenes):
        assert Path(audio_path).exists(), f"Scene {idx} audio must exist"
        print(f" -> Scene {idx} [{sc.scene_type}]: duration = {dur}s | file = {Path(audio_path).name}")
        total_scene_time += dur

    print(f" -> Total calculated video timeline duration: {total_scene_time:.1f}s")
    assert 18.0 <= total_scene_time <= 40.0, f"Expected 18-40s, got {total_scene_time}s"

    # 4. Master Soundtrack Mixing & Ducking
    print("\n[4/4] Testing Master Soundtrack Compositing & Ducking...")
    master_path, master_dur = mix_master_soundtrack(
        scene_audio_data=synced_scenes,
        bg_music_path=str(AUDIO_DIR / "ambient_property.mp3"),
        output_path=str(TEMP_DIR / "test_master_soundtrack.mp3"),
        music_volume=0.12,
    )

    assert Path(master_path).exists(), "Master soundtrack must be generated"
    assert Path(master_path).stat().st_size > 10000, "Master soundtrack must have valid size"

    clip = AudioFileClip(master_path)
    measured_dur = clip.duration
    clip.close()

    print(f" -> Master Soundtrack File: {master_path}")
    print(f" -> Master Duration: {measured_dur:.2f}s (Matches timeline: {abs(measured_dur - total_scene_time) < 1.0})")
    assert abs(measured_dur - total_scene_time) < 1.5, "Soundtrack duration must match total scene duration"

    print("\n" + "=" * 60)
    print("ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase3_tests()
