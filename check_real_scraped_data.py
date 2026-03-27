#!/usr/bin/env python3
"""
Check what sources are being used for Infosys ESG data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.routers.indicators import get_indicator_values
from backend.database.db import get_session

def check_infosys_data_sources():
    """Check data sources for Infosys indicators"""

    company_id = 2
    year = 2024

    db = get_session()
    try:
        print("INFOSYS ESG DATA SOURCES ANALYSIS")
        print("="*50)

        values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

        # Group by source
        sources = {}
        for indicator in values['indicators']:
            source = indicator.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(indicator)

        print(f"TOTAL INDICATORS: {len(values['indicators'])}")
        print()

        for source, indicators in sources.items():
            print(f"{source.upper()}: {len(indicators)} indicators")

            # Show sample values for each source
            for i, indicator in enumerate(indicators[:5], 1):
                indicator_id = indicator.get('indicator_id', 'N/A')
                answer_value = str(indicator.get('answer_value', 'N/A'))
                value_clean = answer_value.replace('₹', 'INR').replace('—', '-')
                value_preview = value_clean[:45] + "..." if len(value_clean) > 45 else value_clean
                print(f"   {i}. {indicator_id}: {value_preview}")

            if len(indicators) > 5:
                print(f"   ... and {len(indicators) - 5} more")
            print()

        # Find ONLY real scraped data
        real_scraped = []
        for indicator in values['indicators']:
            source = indicator.get('source', '')
            if 'scraped_' in source or source in ['scraped', 'historical']:
                real_scraped.append(indicator)

        print(f"REAL SCRAPED DATA ONLY: {len(real_scraped)} indicators")
        for i, indicator in enumerate(real_scraped, 1):
            indicator_id = indicator.get('indicator_id', 'N/A')
            source = indicator.get('source', 'unknown')
            answer_value = str(indicator.get('answer_value', 'N/A'))
            value_clean = answer_value.replace('₹', 'INR').replace('—', '-')
            value_preview = value_clean[:40] + "..." if len(value_clean) > 40 else value_clean
            print(f"   {i:2d}. {indicator_id} | {source:15} | {value_preview}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_infosys_data_sources()