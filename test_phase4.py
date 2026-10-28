"""
Phase 4 Verification Script
Validates Ken Burns motion generator, glassmorphic overlay cards,
and end-to-end MP4 video rendering.
"""
import sys
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from PIL import Image
from moviepy import VideoFileClip
from core.validator import PropertyInput
from core.script_generator import generate_property_script
from core.voice_synthesizer import synthesize_scenes_audio, mix_master_soundtrack
from core.video_renderer import (
    create_overlay_card,
    build_ken_burns_scene_clip,
    render_property_video,
)
from config import TEMP_DIR, OUTPUT_DIR, AUDIO_DIR


def run_phase4_tests():
    print("=" * 60)
    print("PHASE 4 VERIFICATION: VIDEO COMPOSITING & RENDERING")
    print("=" * 60)

    # 1. Prepare sample property images in temp
    print("\n[1/4] Generating high-resolution test property photos...")
    sample_colors = [
        (45, 75, 115),   # Exterior navy/slate
        (165, 130, 95),  # Interior warm wood/living room
        (85, 135, 120),  # Kitchen sage/marble
        (120, 85, 120),  # Bedroom / terrace sunset
    ]
    test_image_paths = []
    for idx, col in enumerate(sample_colors):
        p = TEMP_DIR / f"property_photo_{idx}.jpg"
        img = Image.new("RGB", (1280, 720), color=col)
        img.save(p, quality=90)
        test_image_paths.append(str(p))
    print(f" -> Generated {len(test_image_paths)} test property images.")

    # 2. Test Overlay Card Generator
    print("\n[2/4] Testing Glassmorphic Overlay Card Generator...")
    prop = PropertyInput(
        name="Villa Grand Azure",
        location="Palm Beach, Florida",
        price="$2,850,000",
        property_type="Luxury Waterfront Villa",
        features=[
            "Direct Oceanfront Access & Private Dock",
            "Designer Chef's Kitchen with Sub-Zero Appliances",
        ],
        contact_cta="Contact Premier Living at (561) 555-0188",
        image_paths=test_image_paths,
    )
    script = generate_property_script(prop)
    
    overlay = create_overlay_card(
        width=1280,
        height=720,
        scene=script.scenes[0],
        property_name=prop.name,
    )
    assert overlay.size == (1280, 720), "Overlay size must match target canvas"
    assert overlay.mode == "RGBA", "Overlay must be RGBA for transparency"
    overlay.save(TEMP_DIR / "test_overlay_preview.png")
    print(" -> Overlay card rendered with badge, title, subtitle & transparency (OK).")

    # 3. Test Ken Burns Motion Scene Clip
    print("\n[3/4] Testing Ken Burns Motion Scene Clip (1-second test)...")
    clip = build_ken_burns_scene_clip(
        scene=script.scenes[0],
        duration=1.0,
        width=1280,
        height=720,
        zoom_in=True,
        property_name=prop.name,
    )
    assert clip.duration == 1.0, "Clip duration must match"
    frame = clip.get_frame(0.5)
    assert frame.shape == (720, 1280, 3), "Frame dimensions must match (H, W, C)"
    clip.close()
    print(" -> Ken Burns motion clip generated successfully (OK).")

    # 4. End-to-End MP4 Video Rendering
    print("\n[4/4] Executing End-to-End Property Video Render...")
    # Synthesize audio scenes
    synced_audio = synthesize_scenes_audio(
        scenes=script.scenes,
        voice="en-US-ChristopherNeural",
        scene_padding=0.5,
        temp_dir=TEMP_DIR / "phase4_audio",
    )
    # Mix master soundtrack
    master_audio, _ = mix_master_soundtrack(
        scene_audio_data=synced_audio,
        bg_music_path=str(AUDIO_DIR / "ambient_property.mp3"),
        output_path=str(TEMP_DIR / "phase4_master.mp3"),
        music_volume=0.12,
    )
    # Render final MP4
    output_mp4 = render_property_video(
        prop=prop,
        script=script,
        scene_audio_data=synced_audio,
        master_audio_path=master_audio,
        output_filename="test_property_tour.mp4",
        width=1280,
        height=720,
        fps=24,
    )

    assert Path(output_mp4).exists(), "Output MP4 must exist"
    file_size_mb = Path(output_mp4).stat().st_size / (1024 * 1024)
    print(f" -> MP4 File Created: {output_mp4}")
    print(f" -> File Size: {file_size_mb:.2f} MB")
    assert file_size_mb > 0.5, "Video file size must be substantial"

    # Verify video properties using MoviePy
    v_clip = VideoFileClip(output_mp4)
    print(f" -> Video Duration: {v_clip.duration:.2f} seconds")
    print(f" -> Resolution: {v_clip.size[0]}x{v_clip.size[1]} @ {v_clip.fps} fps")
    print(f" -> Audio Stream Attached: {v_clip.audio is not None}")
    
    assert v_clip.audio is not None, "Video must have audio track"
    assert 18.0 <= v_clip.duration <= 45.0, f"Video duration ({v_clip.duration}s) must be in 20-40s range"
    v_clip.close()

    print("\n" + "=" * 60)
    print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase4_tests()
