"""
Command-Line Interface (CLI) for AI Property Video Generator.

Usage:
    # Run with pre-packaged sample listing 1:
    python cli.py --sample 1

    # Run with a custom JSON listing file:
    python cli.py --input assets/sample_data/listing_1_penthouse/listing_data.json --output output/penthouse_tour.mp4

    # Run with specific voice:
    python cli.py --sample 2 --voice en-IN-NeerjaNeural
"""
import sys
import json
import argparse
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import (
    DEFAULT_TTS_VOICE,
    AUDIO_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
)
from core.validator import validate_property_input, PropertyInput
from core.script_generator import generate_property_script, verify_factual_grounding
from core.voice_synthesizer import (
    synthesize_scenes_audio,
    mix_master_soundtrack,
    AVAILABLE_VOICES,
)
from core.video_renderer import render_property_video


def run_pipeline(
    prop: PropertyInput,
    output_filename: str = "property_tour.mp4",
    voice: str = DEFAULT_TTS_VOICE,
    api_key: str = None,
) -> str:
    """Executes the full video generation pipeline and returns the MP4 path."""
    print("\n" + "=" * 60)
    print(f"🎬 GENERATING PROPERTY VIDEO: {prop.name}")
    print("=" * 60)
    print(f"📍 Location      : {prop.location}")
    print(f"💰 Price         : {prop.price}")
    print(f"🏡 Property Type : {prop.property_type}")
    print(f"📸 Images        : {len(prop.image_paths)} scenes")
    print(f"🎙 Voice         : {voice}")

    # Step 1: AI Script Generation
    print("\n[1/4] Generating Scene Script & Lower-Third Captions...")
    script = generate_property_script(prop, api_key=api_key)
    print(f" -> Engine Used    : {script.engine_used.upper()}")
    print(f" -> Scene Count    : {len(script.scenes)} scenes")
    print(f" -> Est. Duration  : {script.total_estimated_duration}s")
    
    passed_audit, audit_notes = verify_factual_grounding(script, prop)
    for note in audit_notes:
        print(f"    * {note}")

    # Step 2: Neural Speech Synthesis
    print("\n[2/4] Synthesizing Neural Narration with edge-tts...")
    audio_temp_dir = TEMP_DIR / "cli_audio"
    synced_audio_data = synthesize_scenes_audio(
        scenes=script.scenes,
        voice=voice,
        scene_padding=0.5,
        temp_dir=audio_temp_dir,
    )
    for idx, (sc, a_path, dur) in enumerate(synced_audio_data):
        print(f" -> Scene {idx + 1} ({sc.scene_type}): {dur}s | \"{sc.voiceover_text[:60]}...\"")

    # Step 3: Background Audio Mixing & Ducking
    print("\n[3/4] Mixing Master Soundtrack & Applying Ducking...")
    master_audio_path, total_dur = mix_master_soundtrack(
        scene_audio_data=synced_audio_data,
        bg_music_path=str(AUDIO_DIR / "ambient_property.mp3"),
        output_path=str(TEMP_DIR / "cli_master_soundtrack.mp3"),
        music_volume=0.12,
    )
    print(f" -> Soundtrack ready: {total_dur:.1f}s")

    # Step 4: Video Compositing & MP4 Export
    print("\n[4/4] Compositing Ken Burns Motion Video & Exporting MP4...")
    
    def on_progress(fraction, message):
        bar_len = 30
        filled = int(bar_len * fraction)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r [{bar}] {int(fraction * 100)}% - {message}", end="", flush=True)

    output_path = render_property_video(
        prop=prop,
        script=script,
        scene_audio_data=synced_audio_data,
        master_audio_path=master_audio_path,
        output_filename=output_filename,
        width=1280,
        height=720,
        fps=24,
        progress_callback=on_progress,
    )
    print()  # newline after progress bar

    print("\n" + "=" * 60)
    print(f"✅ VIDEO GENERATION COMPLETE!")
    print(f"📁 Output File: {output_path}")
    print(f"⏱ Total Length: {total_dur:.1f} seconds")
    print("=" * 60)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="AI Property Video Generator — Automated promotional real estate video creator"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to JSON file containing property details and image paths",
    )
    parser.add_argument(
        "--sample",
        "-s",
        type=int,
        choices=[1, 2],
        help="Run pre-packaged sample listing (1: Penthouse, 2: Beach Villa)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="property_tour.mp4",
        help="Output MP4 filename (saved in output/ directory)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        type=str,
        default=DEFAULT_TTS_VOICE,
        choices=list(AVAILABLE_VOICES.keys()),
        help="Voice for narration",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optional Google Gemini API key",
    )

    args = parser.parse_args()

    # Determine input source
    if args.sample:
        if args.sample == 1:
            json_path = Path("assets/sample_data/listing_1_penthouse/listing_data.json")
        else:
            json_path = Path("assets/sample_data/listing_2_villa/listing_data.json")
    elif args.input:
        json_path = Path(args.input)
    else:
        print("\n❌ Error: Please specify either --sample [1|2] or --input <path_to_json>.")
        print("Run 'python cli.py --help' for usage examples.\n")
        sys.exit(1)

    if not json_path.exists():
        print(f"\n❌ Error: Listing file not found: {json_path}\n")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"\n❌ Error: Failed to parse JSON file {json_path}: {e}\n")
        sys.exit(1)

    # Resolve relative image paths relative to the JSON file location
    raw_images = data.get("image_paths", [])
    resolved_images = []
    for img_p in raw_images:
        p = Path(img_p)
        if not p.is_absolute():
            resolved = (json_path.parent / p).resolve()
            resolved_images.append(str(resolved))
        else:
            resolved_images.append(str(p))

    # Validate input gracefully
    ok, validated_prop, errors = validate_property_input(
        name=data.get("name", ""),
        location=data.get("location", ""),
        price=data.get("price", ""),
        property_type=data.get("property_type", ""),
        features=data.get("features", []),
        contact_cta=data.get("contact_cta", ""),
        image_paths=resolved_images,
    )

    if not ok:
        print("\n❌ Property Input Validation Failed:")
        for err in errors:
            print(f"  * {err}")
        print("\nPlease fix the issues above and try again.\n")
        sys.exit(1)

    # Run generation
    try:
        run_pipeline(
            prop=validated_prop,
            output_filename=args.output,
            voice=args.voice,
            api_key=args.api_key,
        )
    except Exception as e:
        print(f"\n❌ Fatal Error during video generation: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
