#!/usr/bin/env python3
"""
TEST DYNAMIC SOURCE DISPLAY FIX
Verify that frontend shows correct dynamic sources instead of "manual"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData

def test_source_display_fix():
    """Test that sources are properly preserved and displayed"""

    print("=" * 80)
    print("TESTING DYNAMIC SOURCE DISPLAY FIX")
    print("=" * 80)

    db = get_session()

    # Test companies that have dynamic pattern data
    test_companies = [
        (26, "BANK OF BARODA", 2023),
        (46, "Infosys Limited", 2024)
    ]

    for company_id, company_name, year in test_companies:
        print(f"\nTesting {company_name} (Year: {year}):")
        print("-" * 50)

        # Check scraped data sources
        scraped_records = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"ScrapedData records: {len(scraped_records)}")

        # Group by source type
        source_counts = {}
        for record in scraped_records:
            source = record.source
            source_counts[source] = source_counts.get(source, 0) + 1

        print("Sources in ScrapedData:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} indicators")

        # Check answer sources
        answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        answer_source_counts = {}
        for answer in answers:
            source = answer.source
            answer_source_counts[source] = answer_source_counts.get(source, 0) + 1

        print(f"\nAnswer records: {len(answers)}")
        print("Sources in Answers:")
        for source, count in answer_source_counts.items():
            print(f"  {source}: {count} indicators")

        # Check for dynamic sources
        dynamic_sources = [s for s in source_counts.keys() if 'dynamic' in s or 'enhanced' in s]
        dynamic_in_answers = [s for s in answer_source_counts.keys() if 'dynamic' in s or 'enhanced' in s]

        print(f"\nDynamic sources stored: {len(dynamic_sources)}")
        if dynamic_sources:
            for source in dynamic_sources:
                print(f"  * {source}")

        print(f"Dynamic sources in answers: {len(dynamic_in_answers)}")
        if dynamic_in_answers:
            for source in dynamic_in_answers:
                print(f"  * {source}")
        else:
            print("  WARNING: No dynamic sources preserved in answers")

    print("\n" + "=" * 80)
    print("SOURCE DISPLAY FIX ANALYSIS")
    print("=" * 80)

    # Test the indicator processor
    try:
        from backend.services.indicator_processor import IndicatorProcessor

        processor = IndicatorProcessor()

        # Test with Bank of Baroda
        test_indicator = "IMP-M05-I05"  # Known to have dynamic sustainability data
        result = processor.process_indicator(26, 2023, test_indicator, db)

        if result:
            print(f"\nTesting indicator {test_indicator}:")
            print(f"  Value: {result['value']}")
            print(f"  Source: {result['source']}")
            print(f"  Expected: dynamic_sustainability_patterns")

            if result['source'] == 'dynamic_sustainability_patterns':
                print("  SUCCESS: Dynamic source preserved!")
            elif result['source'] == 'scraped':
                print("  PARTIAL: Still showing generic 'scraped'")
            elif result['source'] == 'manual':
                print("  FAILED: Still showing 'manual'")
            else:
                print(f"  UNKNOWN: Showing '{result['source']}'")
        else:
            print(f"No result for indicator {test_indicator}")

    except Exception as e:
        print(f"Error testing processor: {str(e)}")

    print(f"\nFRONTEND INTEGRATION STATUS:")
    print(f"* Backend fixes: Source priority logic updated")
    print(f"* DataMapper: Preserves specific sources")
    print(f"* SourceBadge: Added dynamic pattern mappings")
    print(f"* Testing required: Run pipeline to verify frontend display")

    db.close()

if __name__ == "__main__":
    test_source_display_fix()