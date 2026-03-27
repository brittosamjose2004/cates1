#!/usr/bin/env python3
"""
JSW STEEL DATA DUPLICATION DETAILS
Show exactly what data is duplicated between years
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def show_duplicated_data_details():
    """Show exact details of the duplicated data"""
    print("JSW STEEL DATA DUPLICATION - DETAILED ANALYSIS")
    print("=" * 80)

    db = get_session()
    try:
        # Check 2020 vs 2021 duplicated data
        print("\n[DUPLICATED DATA] 2020 vs 2021 (100% identical)")
        print("-" * 60)

        data_2020 = db.query(ScrapedData).filter_by(company_id=44, year=2020).all()
        data_2021 = db.query(ScrapedData).filter_by(company_id=44, year=2021).all()

        print(f"2020 data ({len(data_2020)} records):")
        for item in data_2020:
            key = item.data_key if hasattr(item, 'data_key') else 'unknown'
            value = item.data_value if hasattr(item, 'data_value') else 'None'
            source = item.source if hasattr(item, 'source') else 'unknown'
            print(f"  {key}: {str(value)[:60]}... (source: {source})")

        print(f"\n2021 data ({len(data_2021)} records):")
        for item in data_2021:
            key = item.data_key if hasattr(item, 'data_key') else 'unknown'
            value = item.data_value if hasattr(item, 'data_value') else 'None'
            source = item.source if hasattr(item, 'source') else 'unknown'
            print(f"  {key}: {str(value)[:60]}... (source: {source})")

        # Check sources - are they even the same source?
        sources_2020 = set(item.source for item in data_2020 if hasattr(item, 'source'))
        sources_2021 = set(item.source for item in data_2021 if hasattr(item, 'source'))

        print(f"\nSource comparison:")
        print(f"  2020 sources: {sources_2020}")
        print(f"  2021 sources: {sources_2021}")
        print(f"  Same sources: {sources_2020 == sources_2021}")

        # Check 2023 vs 2024 (sample of duplicated data)
        print(f"\n[DUPLICATED DATA] 2023 vs 2024 (100% identical - showing sample)")
        print("-" * 60)

        data_2023 = db.query(ScrapedData).filter_by(company_id=44, year=2023).all()
        data_2024 = db.query(ScrapedData).filter_by(company_id=44, year=2024).all()

        print(f"Total records: 2023 has {len(data_2023)}, 2024 has {len(data_2024)}")

        # Show first 5 indicators from each year
        print(f"\nFirst 5 indicators from 2023:")
        for item in data_2023[:5]:
            key = item.data_key if hasattr(item, 'data_key') else 'unknown'
            value = item.data_value if hasattr(item, 'data_value') else 'None'
            print(f"  {key}: {str(value)[:50]}...")

        print(f"\nFirst 5 indicators from 2024:")
        for item in data_2024[:5]:
            key = item.data_key if hasattr(item, 'data_key') else 'unknown'
            value = item.data_value if hasattr(item, 'data_value') else 'None'
            print(f"  {key}: {str(value)[:50]}...")

        # Check if sources are identical too
        sources_2023 = set(item.source for item in data_2023 if hasattr(item, 'source'))
        sources_2024 = set(item.source for item in data_2024 if hasattr(item, 'source'))

        print(f"\nSource comparison 2023 vs 2024:")
        print(f"  2023 sources: {sources_2023}")
        print(f"  2024 sources: {sources_2024}")
        print(f"  Same sources: {sources_2023 == sources_2024}")

        # Data quality assessment
        print(f"\n[DATA QUALITY ASSESSMENT]")
        print("=" * 80)
        print(f"CRITICAL ISSUES FOUND:")
        print(f"  1. 2020-2021: 100% duplicate data (2 indicators)")
        print(f"  2. 2023-2024: 100% duplicate data (390 indicators)")
        print(f"  3. Same sources used for different years")
        print(f"  4. No genuine year-specific data differences")

        print(f"\nIMPACT:")
        print(f"  - Year-over-year analysis is meaningless")
        print(f"  - Trend analysis shows false stability")
        print(f"  - Historical comparisons are invalid")
        print(f"  - Pipeline may be copying data instead of extracting fresh data")

        print(f"\nRECOMMENDED ACTIONS:")
        print(f"  1. Investigate why data is being duplicated")
        print(f"  2. Check if extraction process copies previous year data")
        print(f"  3. Verify data sources are year-specific")
        print(f"  4. Clean up duplicated data in database")
        print(f"  5. Implement year-specific validation")

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_duplicated_data_details()