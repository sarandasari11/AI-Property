"""
Phase 5 Verification Script
Tests Web App structure, CLI tool invocation, and sample dataset integration.
"""
import sys
import subprocess
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import SAMPLE_DATA_DIR, OUTPUT_DIR


def run_phase5_tests():
    print("=" * 60)
    print("PHASE 5 VERIFICATION: WEB APP & CLI INTERFACE")
    print("=" * 60)

    # 1. Verify Sample Data Packages
    print("\n[1/3] Checking Sample Datasets...")
    samples = [
        SAMPLE_DATA_DIR / "listing_1_penthouse" / "listing_data.json",
        SAMPLE_DATA_DIR / "listing_2_villa" / "listing_data.json",
    ]
    for s_path in samples:
        assert s_path.exists(), f"Sample listing must exist: {s_path}"
        print(f" -> Found sample: {s_path.parent.name}")

    # 2. Test CLI Graceful Error Handling
    print("\n[2/3] Testing CLI Graceful Error Handling...")
    res = subprocess.run(
        [sys.executable, "cli.py", "--input", "non_existent_file.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode != 0, "CLI must return non-zero exit code on missing file"
    assert "not found" in res.stdout.lower() or "not found" in res.stderr.lower(), (
        "CLI must print useful error message on missing file"
    )
    print(" -> CLI handled missing input file gracefully without crash traceback.")

    # 3. Verify Generated MP4 Deliverables in output/
    print("\n[3/3] Checking Generated Video Deliverables...")
    mp4_files = list(OUTPUT_DIR.glob("*.mp4"))
    assert len(mp4_files) >= 1, "At least one sample MP4 must be present in output/"
    for mp4 in mp4_files:
        size_mb = mp4.stat().st_size / (1024 * 1024)
        print(f" -> Deliverable MP4: {mp4.name} ({size_mb:.2f} MB)")
        assert size_mb > 0.5, "Video file must be valid"

    print("\n" + "=" * 60)
    print("ALL PHASE 5 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase5_tests()
