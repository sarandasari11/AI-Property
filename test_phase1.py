"""
Phase 1 Smoke Test & Verification Script
Validates environment dependencies, core configurations, and input validation.
"""
import sys
from pathlib import Path
from PIL import Image

from config import BASE_DIR, OUTPUT_DIR, TEMP_DIR, MIN_PROPERTY_IMAGES, MAX_PROPERTY_IMAGES
from core.validator import validate_property_input


def run_tests():
    print("=" * 60)
    print("PHASE 1 VERIFICATION & SMOKE TEST")
    print("=" * 60)

    # 1. Directory Checks
    print("\n[1/4] Checking project directories...")
    assert BASE_DIR.exists(), "BASE_DIR must exist"
    assert OUTPUT_DIR.exists(), "OUTPUT_DIR must exist"
    assert TEMP_DIR.exists(), "TEMP_DIR must exist"
    print(" -> Directories OK.")

    # 2. Dependency imports
    print("\n[2/4] Testing library imports...")
    import moviepy
    import edge_tts
    import streamlit
    import pydantic
    print(f" -> moviepy: {moviepy.__version__}")
    print(f" -> edge_tts: {edge_tts.__version__}")
    print(f" -> streamlit: {streamlit.__version__}")
    print(f" -> pydantic: {pydantic.__version__}")
    print(" -> Imports OK.")

    # 3. Test Validator - Failure Cases (Graceful Error Handling)
    print("\n[3/4] Testing Validator Graceful Error Handling...")
    
    # Case A: Missing fields
    ok, model, errors = validate_property_input(
        name="",
        location="",
        price="",
        property_type="",
        features=[],
        contact_cta="",
        image_paths=[]
    )
    assert not ok, "Validation should fail for empty inputs"
    assert len(errors) >= 2, f"Should return multiple descriptive errors, got: {errors}"
    print(f" -> Correctly caught empty input with {len(errors)} error messages:")
    for err in errors[:3]:
        print(f"    * {err}")

    # Case B: Insufficient images (< 4 images)
    dummy_img = TEMP_DIR / "dummy_test.jpg"
    img = Image.new("RGB", (640, 480), color=(73, 109, 137))
    img.save(dummy_img)

    ok, model, errors = validate_property_input(
        name="Test Villa",
        location="Miami, FL",
        price="$1,200,000",
        property_type="Luxury Villa",
        features=["Pool", "Ocean View"],
        contact_cta="Call 555-0100",
        image_paths=[str(dummy_img)]  # Only 1 image
    )
    assert not ok, "Should reject less than 4 images"
    assert any("Insufficient images" in e for e in errors), "Must explicitly report insufficient images"
    print(" -> Correctly reported insufficient image count (< 4).")

    # 4. Test Validator - Success Case (4 valid images)
    print("\n[4/4] Testing Validator with Valid Inputs (4 images)...")
    valid_imgs = []
    for i in range(4):
        test_file = TEMP_DIR / f"test_img_{i}.jpg"
        img = Image.new("RGB", (1280, 720), color=(50 + i * 30, 80 + i * 20, 120))
        img.save(test_file)
        valid_imgs.append(str(test_file))

    ok, model, errors = validate_property_input(
        name="Sunset Azure Penthouse",
        location="Malibu, CA",
        price="$3,500,000",
        property_type="Luxury Penthouse",
        features=["Panoramic Ocean Views", "Private Infinity Pool", "Smart Home Automation", "Italian Marble Flooring"],
        contact_cta="Contact agent at (310) 555-0199 or visit luxuryrealty.com",
        image_paths=valid_imgs
    )
    assert ok, f"Validation should succeed for valid inputs, got errors: {errors}"
    assert model is not None
    assert len(model.image_paths) == 4
    assert model.name == "Sunset Azure Penthouse"
    print(" -> Valid property input validated successfully!")

    print("\n" + "=" * 60)
    print("ALL PHASE 1 SMOKE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
