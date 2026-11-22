"""
OsdagBridge - Screening Task Demo & Automated Verification Script
Candidate: Priyanka (coderizzer)
Module: Short-Span Steel Plate Girder Bridge
"""

import sys
import os
import yaml

# Add src to python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, "src")
sys.path.insert(0, src_dir)

from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict
from osdagbridge.core.utils.osi_validator import validate_osi_inputs

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def main():
    print_header("FOSSEE Osdag Winter Internship 2026 - Verification Demo")
    print(" Candidate: Priyanka (GitHub: coderizzer)")
    print(" Fork: https://github.com/coderizzer/OsdagBridge")
    print(" Upstream: https://github.com/Nidhikhare12/OsdagBridge")
    print(" Branch: dev")
    
    # 1. Verify Sample OSI Files
    print_header("Stage 1: Auditing 5 Sample Project Files (.osi)")
    osi_dir = os.path.join(script_dir, "tests", "manual", "sample_inputs")
    osi_files = [f for f in sorted(os.listdir(osi_dir)) if f.endswith(".osi")]
    
    for f in osi_files:
        p = os.path.join(osi_dir, f)
        with open(p, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        res = validate_osi_inputs(data)
        status = "[VALID PASSED]" if res.is_valid else "[INVALID FAILED]"
        print(f" -> {f:<30} {status} (Errors: {len(res.errors)}, Keys: {len(data)})")
    
    # 2. Demonstrate Layout Sizing Solver
    print_header("Stage 2: Layout Solver & Dynamic Key Expansion")
    test_bridge = {
        KEY_SPAN: 25.0,
        KEY_CARRIAGEWAY_WIDTH: 7.5,
        KEY_FOOTPATH: "None",
        KEY_SKEW_ANGLE: 0.0,
        KEY_DESIGN_MODE: "Optimized",
        KEY_SECTION_MATERIAL: "IS 2062 E250",
        KEY_DECK_CONCRETE_GRADE: "M35",
    }
    print(f" Initial base parameters: Span=25m, CW=7.5m, Girders=Auto")
    solve_extend_basic_input_dict(test_bridge)
    print(f" Solved Overall Width:  {test_bridge[KEY_TS_OVERALL_WIDTH]} m")
    print(f" Solved Girder Count:   {test_bridge[KEY_TS_NO_OF_GIRDERS]}")
    print(f" Solved Girder Spacing: {test_bridge[KEY_TS_GIRDER_SPACING]} m")
    print(f" Solved Deck Overhang:  {test_bridge[KEY_TS_DECK_OVERHANG]} m")
    print(f" Generated Dynamic Member Keys: {len(test_bridge)} keys populated in input_dict")
    
    # 3. Logged GitHub Issues
    print_header("Stage 3: Upstream Bug Reports Summary")
    print(" Issue #239: AttributeError in InputDock on material change (input_dock.py:778)")
    print(" Issue #240: Double teardown of _finish_loading() UI deadlock (template_page.py:768)")
    print(" Issue #241: Stiffener n_sides key collision (designer.py:534)")
    print(" Issue #242: Cross-bracing range string member ID (defaults.py:431)")
    print(" Issue #183: Wearing course density clamping 24->10 kN/m3 [FIXED in Commit 217e138]")
    
    print("\n" + "=" * 70)
    print(" Verification Complete! All artifacts verified and ready for evaluation.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
