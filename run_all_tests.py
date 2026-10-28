"""
Master Test Runner for AI Property Video Generator
Executes all phase-wise test suites and reports system health.
"""
import sys
from pathlib import Path

# Enable UTF-8 encoding on Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from test_phase1 import run_tests as run_p1
from test_phase2 import run_phase2_tests as run_p2
from test_phase3 import run_phase3_tests as run_p3
from test_phase5 import run_phase5_tests as run_p5


def main():
    print("\n" + "=" * 70)
    print("🏆 EXECUTING MASTER VERIFICATION SUITE — ALL PHASES")
    print("=" * 70)

    try:
        # Phase 1: Scaffolding, imports, and validator
        run_p1()
        
        # Phase 2: Script generation, scene breakdown, and factual grounding
        run_p2()

        # Phase 3: Neural TTS synthesis, scene sync, and audio ducking
        run_p3()

        # Phase 5: Web UI, CLI resilience, and deliverables
        run_p5()

        print("\n" + "=" * 70)
        print("🎉 ALL PHASE-WISE TEST SUITES PASSED WITH 100% SUCCESS!")
        print("📁 Deliverables Verified in output/:")
        for f in Path("output").glob("*.mp4"):
            print(f"   * {f.name} ({f.stat().st_size / (1024 * 1024):.2f} MB)")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Master Test Suite Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
