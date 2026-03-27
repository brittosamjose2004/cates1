#!/usr/bin/env python3
"""
Get ONLY real scraped ESG data from company documents
NO intelligent defaults - pure document extraction only
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.routers.indicators import get_indicator_values
from backend.database.db import get_session

def get_only_real_scraped_data(company_id, year=2024):
    """Get ONLY indicators with real scraped data from documents"""

    db = get_session()
    try:
        print("REAL DOCUMENT-BASED ESG DATA ONLY")
        print("="*50)
        print(f"Company ID: {company_id} | Year: {year}")
        print("NO intelligent defaults - ONLY real scraped data")
        print("="*50)

        # Get all indicators
        values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

        # Filter for ONLY real scraped data sources
        real_scraped_sources = [
            'scraped', 'historical', 'scraped_brsr_pdf',
            'scraped_yahoo_historical', 'scraped_yahoo',
            'scraped_pdf', 'scraped_csv'
        ]

        real_indicators = [
            indicator for indicator in values['indicators']
            if indicator.get('source', '') in real_scraped_sources
        ]

        print(f"REAL SCRAPED DATA FOUND: {len(real_indicators)}/151 indicators")

        # Group by source
        by_source = {}
        for indicator in real_indicators:
            source = indicator.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(indicator)

        for source, indicators in by_source.items():
            print(f"\n{source.upper()}: {len(indicators)} indicators")

        # Show all real scraped indicators
        print(f"\nALL REAL SCRAPED INDICATORS:")
        for i, indicator in enumerate(real_indicators, 1):
            indicator_id = indicator.get('indicator_id', 'N/A')
            source = indicator.get('source', 'unknown')
            answer_value = str(indicator.get('answer_value', 'N/A'))

            # Clean the value for display
            value_clean = answer_value.replace('₹', 'INR').replace('—', '-')
            value_preview = value_clean[:40] + "..." if len(value_clean) > 40 else value_clean

            print(f"{i:2d}. {indicator_id} | {source:15} | {value_preview}")

        print(f"\nSUMMARY:")
        print(f"Real scraped indicators: {len(real_indicators)}")
        print(f"Document sources: {len(by_source)}")
        print(f"Zero artificial data - ALL from real company documents")

        return real_indicators

    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        db.close()

def create_pure_scraped_company_data(company_id, year=2024):
    """Create a version with ONLY real scraped data (no intelligent defaults)"""

    # This would remove all intelligent_default indicators and keep only real scraped data
    from backend.database.db import get_session
    from backend.database.models import Answer

    db = get_session()
    try:
        print(f"CREATING PURE SCRAPED DATA VERSION")
        print(f"Removing all intelligent_default indicators...")

        # Remove intelligent defaults
        deleted = db.query(Answer).filter_by(
            company_id=company_id,
            year=year,
            source="intelligent_default"
        ).delete()

        db.commit()
        print(f"Removed {deleted} intelligent default indicators")
        print(f"Now showing ONLY real scraped data from company documents")

        return deleted

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--company_id", type=int, default=2, help="Company ID")
    parser.add_argument("--pure", action="store_true", help="Remove intelligent defaults")

    args = parser.parse_args()

    if args.pure:
        create_pure_scraped_company_data(args.company_id)

    get_only_real_scraped_data(args.company_id)