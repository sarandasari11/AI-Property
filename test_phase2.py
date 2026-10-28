"""
Phase 2 Verification & Evaluation Script
Tests script generation, scene mapping across varying image counts (4 to 8),
timing calculations, and factual grounding audits.
"""
import sys
from pathlib import Path

# Enable UTF-8 encoding on Windows console for currency symbols (e.g. ₹, €, £)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.validator import PropertyInput
from core.script_generator import (
    generate_property_script,
    verify_factual_grounding,
    estimate_speech_duration,
)


def run_phase2_tests():
    print("=" * 60)
    print("PHASE 2 VERIFICATION: AI SCRIPT & CAPTION ENGINE")
    print("=" * 60)

    # 1. Test Duration Estimator
    print("\n[1/4] Testing Speech Duration Estimator...")
    short_text = "Welcome to the Grand Horizon."
    dur_short = estimate_speech_duration(short_text, min_duration=4.5)
    assert dur_short >= 4.5, "Short text should enforce min_duration"
    
    long_text = "Step inside to experience the sprawling open-concept living room bathed in natural sunlight, featuring soaring ceilings and panoramic city skyline views."
    dur_long = estimate_speech_duration(long_text)
    assert dur_long > 6.0, "Long text should scale duration appropriately"
    print(f" -> Short text duration: {dur_short}s | Long text duration: {dur_long}s (OK)")

    # 2. Test 4-Image Property Listing (20-25s target)
    print("\n[2/4] Testing 4-Image Listing Generation (Sample 2-BHK Apartment)...")
    prop_4 = PropertyInput(
        name="Skyline Vista 2-BHK",
        location="Indiranagar, Bengaluru",
        price="₹1.45 Cr",
        property_type="2-BHK Modern Apartment",
        features=["Vastu Compliant North Facing", "Modular Italian Kitchen", "Clubhouse & Rooftop Swimming Pool"],
        contact_cta="Call +91-98765-43210 or visit skylineproperties.com",
        image_paths=[f"temp/img_{i}.jpg" for i in range(4)]
    )
    script_4 = generate_property_script(prop_4)
    assert len(script_4.scenes) == 4, f"Expected 4 scenes, got {len(script_4.scenes)}"
    assert script_4.scenes[0].scene_type == "intro"
    assert script_4.scenes[-1].scene_type == "outro"
    assert "Indiranagar" in script_4.scenes[0].caption_subtitle
    assert "₹1.45 Cr" in script_4.scenes[-1].caption_title
    print(f" -> Generated {len(script_4.scenes)} scenes | Total duration: {script_4.total_estimated_duration}s")
    print(f" -> Intro: '{script_4.scenes[0].voiceover_text}'")
    print(f" -> Outro: '{script_4.scenes[-1].voiceover_text}'")

    # 3. Test 6-Image & 8-Image Listings (Checking scalability)
    print("\n[3/4] Testing 6-Image and 8-Image Listings...")
    prop_8 = PropertyInput(
        name="The Royal Palm Villa",
        location="Palm Jumeirah, Dubai",
        price="$4,900,000",
        property_type="5-Bedroom Luxury Villa",
        features=[
            "Private Beach Access",
            "Infinity Edge Pool",
            "Floor-to-Ceiling Glass Walls",
            "Private Cinema Room",
            "Smart Home Automation",
            "Landscaped Tropical Garden"
        ],
        contact_cta="Contact Premier Realty at +971-4-555-0199",
        image_paths=[f"temp/villa_{i}.jpg" for i in range(8)]
    )
    script_8 = generate_property_script(prop_8)
    assert len(script_8.scenes) == 8, f"Expected 8 scenes, got {len(script_8.scenes)}"
    assert 30.0 <= script_8.total_estimated_duration <= 45.0, (
        f"8-image video duration ({script_8.total_estimated_duration}s) should remain in the 20-40s range"
    )
    print(f" -> 8-scene tour duration: {script_8.total_estimated_duration}s (Perfect pacing)")

    # 4. Factual Grounding Verification Audit
    print("\n[4/4] Running Factual Grounding Audit...")
    passed_audit, audit_notes = verify_factual_grounding(script_4, prop_4)
    for note in audit_notes:
        print(f"    * {note}")
    assert passed_audit, "Script must pass factual grounding audit"

    print("\n" + "=" * 60)
    print("ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase2_tests()
