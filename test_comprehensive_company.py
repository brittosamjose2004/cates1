#!/usr/bin/env python3
"""
Test the comprehensive ESG test company to verify all 151 indicators are accessible
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
from backend.database.db import get_session

def test_comprehensive_company():
    """Test the comprehensive test company indicators"""
    company_id = 37  # COMPREHENSIVE ESG TEST COMPANY
    year = 2024

    db = get_session()

    try:
        print("="*80)
        print(f"TESTING COMPREHENSIVE ESG TEST COMPANY")
        print(f"Company ID: {company_id}")
        print(f"Year: {year}")
        print("="*80)

        # 1. Get summary
        print("\n1. INDICATOR SUMMARY:")
        summary = get_indicator_summary(company_id, year, db)

        overall = summary['overall_summary']
        print(f"   Overall completion rate: {overall['completion_rate']}%")
        print(f"   Indicators with values: {overall['indicators_with_values']}/151")
        if 'total_modules' in overall:
            print(f"   Total modules: {overall['total_modules']}")
        if 'modules_with_data' in overall:
            print(f"   Modules with data: {overall['modules_with_data']}")

        print("\n   Module breakdown:")
        for module in summary['module_breakdown'][:10]:
            print(f"     {module['module_name'][:50]:50}: {module['completion_rate']:5.1f}% ({module['indicators_with_values']}/{module['total_indicators']})")

        if len(summary['module_breakdown']) > 10:
            print(f"     ... and {len(summary['module_breakdown']) - 10} more modules")

        # 2. Get all indicator values
        print(f"\n2. ALL INDICATOR VALUES:")
        values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

        print(f"   Found {len(values['indicators'])} indicators with data:")

        # Show first 20 actual values
        print(f"\n   Sample indicator values (showing first 20):")
        for i, indicator in enumerate(values['indicators'][:20], 1):
            indicator_id = indicator.get('indicator_id', 'N/A')
            answer_value = indicator.get('answer_value', 'N/A')
            value_preview = str(answer_value)[:60] + "..." if len(str(answer_value)) > 60 else str(answer_value)
            print(f"   {i:2d}. {indicator_id:12} | {value_preview}")

        # Count by source (if available)
        sources = {}
        for indicator in values['indicators']:
            source = indicator.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        print(f"\n   Data sources breakdown:")
        for source, count in sources.items():
            print(f"     {source:12}: {count:3d} indicators")

        # 3. Standard breakdown
        print(f"\n3. STANDARD BREAKDOWN:")
        for standard in ["BRSR", "CDP", "EcoVadis", "GRI"]:
            std_values = get_indicator_values(company_id, year, db, include_empty=False, standard=standard)
            print(f"   {standard:8}: {len(std_values['indicators'])} indicators with values")

        # 4. Success verification
        print(f"\n4. SUCCESS VERIFICATION:")
        if overall['indicators_with_values'] >= 151:
            print("   STATUS: SUCCESS! All 151 indicators populated")
            print("   The comprehensive test company is ready for frontend testing")
        else:
            print(f"   STATUS: PARTIAL - Only {overall['indicators_with_values']}/151 indicators populated")
            print("   Additional work may be needed")

        print(f"\nNEXT STEPS:")
        print(f"1. Start the FastAPI server: uvicorn backend.api.main:app --reload --port 8000")
        print(f"2. Open the frontend application")
        print(f"3. Run the ESG Pipeline for company 'COMPREHENSIVE ESG TEST COMPANY'")
        print(f"4. Verify all 151 indicators show data values in the UI")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_comprehensive_company()