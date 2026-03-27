#!/usr/bin/env python3
"""
RUN PIPELINE WITH SOURCE FIX
Test the complete pipeline with dynamic source preservation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_pipeline_with_source_fix():
    """Run pipeline to regenerate answers with correct dynamic sources"""

    print("=" * 80)
    print("RUNNING PIPELINE WITH SOURCE FIX")
    print("=" * 80)

    # Test with Bank of Baroda (has dynamic sources)
    company_id = 26
    year = 2023

    try:
        from comprehensive_pipeline import run_comprehensive_pipeline

        print(f"Running comprehensive pipeline for Bank of Baroda (ID: {company_id}, Year: {year})")
        print("This should regenerate Answer records with correct dynamic sources...")
        print()

        result = run_comprehensive_pipeline(company_id, year)

        if result.get('success'):
            print("PIPELINE SUCCESS!")
            print(f"Indicators processed: {result.get('indicators_processed', 0)}")

            # Check the Answer records now
            from backend.database.db import get_session
            from backend.database.models import Answer

            db = get_session()
            answers = db.query(Answer).filter_by(
                company_id=company_id,
                year=year
            ).all()

            # Group by source
            source_counts = {}
            for answer in answers:
                source = answer.source
                source_counts[source] = source_counts.get(source, 0) + 1

            print(f"\nREGENERATED ANSWER SOURCES:")
            for source, count in source_counts.items():
                print(f"  {source}: {count} indicators")

            # Check for dynamic sources
            dynamic_sources = [s for s in source_counts.keys() if 'dynamic' in s or 'enhanced' in s]
            if dynamic_sources:
                print(f"\n✓ SUCCESS: Dynamic sources preserved in answers!")
                for source in dynamic_sources:
                    print(f"    - {source}")
                return True
            else:
                print(f"\n✗ ISSUE: Still no dynamic sources in answers")
                return False

            db.close()

        else:
            print(f"PIPELINE FAILED: {result.get('error')}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_pipeline_with_source_fix()

    if success:
        print("\n" + "=" * 80)
        print("DYNAMIC SOURCE FIX SUCCESSFUL!")
        print("=" * 80)
        print("Next steps:")
        print("1. Test frontend to verify dynamic sources are displayed")
        print("2. Sources should show as 'Dynamic ESG', 'Dynamic IT Patterns', etc.")
        print("3. No more 'manual' for dynamic web-scraped data!")
    else:
        print("\n" + "=" * 80)
        print("SOURCE FIX NEEDS FURTHER DEBUG")
        print("=" * 80)
        print("Check backend logs for specific error messages")