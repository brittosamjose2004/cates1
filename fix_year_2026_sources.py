#!/usr/bin/env python3
"""
QUICK FIX: Run pipeline for Year 2026
This will populate Year 2026 with dynamic sources instead of manual ones
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def fix_year_2026():
    """Run pipeline for Bank of Baroda 2026 to get dynamic sources"""

    print("=" * 80)
    print("FIXING YEAR 2026 WITH DYNAMIC SOURCES")
    print("=" * 80)

    # Run pipeline for Bank of Baroda 2026
    company_id = 26
    year = 2026

    try:
        from comprehensive_pipeline import run_comprehensive_pipeline

        print(f"Running comprehensive pipeline for Bank of Baroda")
        print(f"Company ID: {company_id}")
        print(f"Year: {year} (the year frontend is requesting)")
        print()

        result = run_comprehensive_pipeline(company_id, year)

        if result.get('success'):
            print("PIPELINE SUCCESS!")
            print(f"Year 2026 should now have dynamic sources instead of 'manual'")

            # Check the results
            from backend.database.db import get_session
            from backend.database.models import Answer

            db = get_session()
            answers = db.query(Answer).filter_by(
                company_id=company_id,
                year=year
            ).all()

            # Count sources
            source_counts = {}
            dynamic_count = 0

            for answer in answers:
                source = answer.source
                source_counts[source] = source_counts.get(source, 0) + 1

                if 'dynamic' in source or 'enhanced' in source:
                    dynamic_count += 1

            print(f"\nYEAR 2026 UPDATED SOURCES:")
            for source, count in source_counts.items():
                print(f"  {source}: {count} indicators")

            if dynamic_count > 0:
                print(f"\n✓ SUCCESS: {dynamic_count} dynamic indicators in year 2026!")
                print(f"Frontend should now show dynamic sources instead of 'manual'")
                return True
            else:
                print(f"\n⚠️  PARTIAL: No dynamic sources added to year 2026")
                return False

            db.close()

        else:
            print(f"PIPELINE FAILED: {result.get('error')}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_year_2026()

    if success:
        print("\n" + "=" * 80)
        print("YEAR 2026 FIX COMPLETE!")
        print("=" * 80)
        print("Next steps:")
        print("1. Refresh your browser (Ctrl+F5)")
        print("2. Navigate to Bank of Baroda")
        print("3. Sources should now show dynamic sources instead of 'manual'")
    else:
        print("\n" + "=" * 80)
        print("MANUAL FIX REQUIRED")
        print("=" * 80)
        print("Alternative solution:")
        print("1. Add ?year=2023 to frontend URL to force year 2023")
        print("2. Or check SmartYearResolver to prefer dynamic sources")