#!/usr/bin/env python3
"""
TEST FRONTEND PIPELINE INTEGRATION
Test the integrated pipeline with target 151 indicators system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from frontend_pipeline_integration import format_pipeline_progress_message, get_pipeline_151_status

def test_pipeline_integration():
    """Test the pipeline integration with JSW Steel 2023"""
    print("[TEST] Frontend Pipeline Integration")
    print("=" * 80)

    company_id = 44  # JSW Steel Limited
    year = 2023

    print(f"Testing company ID: {company_id}, year: {year}")
    print("-" * 80)

    # Test 1: Progress message formatting
    print("[TEST 1] Progress message formatting:")
    main_msg, details = format_pipeline_progress_message(company_id, year)
    print(f"Main: {main_msg}")
    for i, detail in enumerate(details, 1):
        print(f"Detail {i}: {detail}")

    # Test 2: Detailed status
    print(f"\n[TEST 2] Detailed status breakdown:")
    found_count, total_count, coverage_percent, module_stats, missing = get_pipeline_151_status(company_id, year)

    print(f"Found: {found_count}/{total_count} indicators")
    print(f"Coverage: {coverage_percent:.1f}%")
    print(f"Missing count: {len(missing)}")

    if missing:
        print(f"Missing indicators: {missing[:5]}{'...' if len(missing) > 5 else ''}")

    # Test 3: Module breakdown
    if module_stats:
        print(f"\n[TEST 3] Module statistics:")
        complete_modules = []
        partial_modules = []
        empty_modules = []

        for module, stats in module_stats.items():
            if stats['found'] == stats['total']:
                complete_modules.append(module)
            elif stats['found'] > 0:
                partial_modules.append(f"{module} ({stats['found']}/{stats['total']})")
            else:
                empty_modules.append(module)

        print(f"Complete modules ({len(complete_modules)}): {', '.join(complete_modules)}")
        if partial_modules:
            print(f"Partial modules ({len(partial_modules)}): {', '.join(partial_modules)}")
        if empty_modules:
            print(f"Empty modules ({len(empty_modules)}): {', '.join(empty_modules)}")

    print("\n" + "=" * 80)
    print("[INTEGRATION TEST COMPLETE]")
    print(f"✅ Ready for frontend pipeline: {found_count}/{total_count} indicators ({coverage_percent:.1f}%)")

if __name__ == "__main__":
    test_pipeline_integration()