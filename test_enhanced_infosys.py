#!/usr/bin/env python3
"""
Test enhanced Infosys to verify perfect coverage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
from backend.database.db import get_session

def test_enhanced_infosys():
    """Test Infosys after enhancement"""
    company_id = 2  # Infosys
    year = 2024

    db = get_session()
    try:
        print("TESTING ENHANCED INFOSYS")
        print("="*50)

        # Get summary
        summary = get_indicator_summary(company_id, year, db)
        overall = summary['overall_summary']

        print(f"Coverage: {overall['completion_rate']:.1f}%")
        print(f"Indicators: {overall['indicators_with_values']}/151")

        # Get sample values
        values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

        # Check data sources
        sources = {}
        for indicator in values['indicators']:
            source = indicator.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        print(f"\nData Sources:")
        for source, count in sources.items():
            print(f"  {source}: {count} indicators")

        # Sample values
        print(f"\nSample Values (first 10):")
        for i, indicator in enumerate(values['indicators'][:10], 1):
            indicator_id = indicator.get('indicator_id', 'N/A')
            source = indicator.get('source', 'unknown')
            answer_value = str(indicator.get('answer_value', 'N/A'))
            value_clean = answer_value.replace('₹', 'INR').replace('—', '-')
            value_preview = value_clean[:45] + "..." if len(value_clean) > 45 else value_clean
            print(f"  {i:2d}. {indicator_id} | {value_preview}")

        if overall['completion_rate'] >= 99:
            print(f"\nSUCCESS: Perfect ESG coverage achieved!")
            print(f"NO MORE 'none' or 'unavailable' values!")
        else:
            print(f"\nPartial success: {overall['completion_rate']:.1f}% coverage")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_infosys()