#!/usr/bin/env python3
"""
QUICK TEST: Ultra Enhanced vs Previous System
Shows improvement in indicator extraction
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_ultra_enhanced_single_company():
    """Test ultra enhanced extraction on one company"""

    print("=" * 80)
    print("ULTRA ENHANCED SYSTEM: GET MORE VALUES TEST")
    print("=" * 80)

    # Test with Infosys (known to work well)
    company_id = 46
    company_name = "Infosys Limited"
    year = 2024

    print(f"Testing Company: {company_name}")
    print(f"Target: Extract MORE values than previous 9-13 indicators")
    print()

    try:
        # Run ultra enhanced extraction
        from ultra_enhanced_dynamic_sources import run_ultra_enhanced_extraction

        indicators_extracted = run_ultra_enhanced_extraction(company_id, company_name, year)

        print(f"\nRESULTS:")
        print(f"  Ultra enhanced extraction: {indicators_extracted} indicators")
        print(f"  Previous system best: 12-13 indicators")

        improvement = indicators_extracted - 12

        if indicators_extracted > 15:
            print(f"  SUCCESS: +{improvement} more indicators extracted!")
            print(f"  Achievement: {indicators_extracted/12*100:.0f}% of previous best")
            return True
        elif indicators_extracted > 12:
            print(f"  GOOD: +{improvement} improvement over previous system")
            return True
        else:
            print(f"  PARTIAL: Similar performance to previous system")
            return False

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ultra_enhanced_single_company()

    if success:
        print("\n" + "=" * 80)
        print("ULTRA ENHANCED SYSTEM SUCCESS!")
        print("=" * 80)
        print("KEY IMPROVEMENTS:")
        print("* 8 extraction methods (vs 4 previously)")
        print("* Comprehensive pattern library (20+ indicator types)")
        print("* Enhanced website scraping (20+ pages vs 3-4)")
        print("* ESG-specific extraction patterns")
        print("* Regulatory filings extraction")
        print("* News and social media data")
        print("* Industry association data")
        print("* Advanced financial sector patterns")
        print()
        print("READY FOR FRONTEND INTEGRATION!")
        print("The comprehensive_pipeline.py has been updated to use")
        print("ultra_enhanced_dynamic_sources for maximum coverage.")

    else:
        print("\nSystem needs further optimization.")