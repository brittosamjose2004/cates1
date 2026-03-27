#!/usr/bin/env python3
"""
Debug script to analyze the indicator mapping problem
39 indicators found by comprehensive pipeline → only 5/151 counted
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Answer, ScrapedData


def debug_indicator_mapping():
    """Debug why 39 indicators → only 5/151 counted"""

    print("=== DEBUGGING INDICATOR MAPPING ISSUE ===")

    db = get_session()

    # Step 1: Check data conversion
    print("\nStep 1: Data Conversion Analysis")
    scraped_count = db.query(ScrapedData).filter_by(company_id=14, year=2024).count()
    answer_count = db.query(Answer).filter_by(company_id=14, year=2024).count()

    print(f"  ScrapedData records: {scraped_count}")
    print(f"  Answer records: {answer_count}")

    # Step 2: Sample indicators from each stage
    print("\nStep 2: Sample Indicator IDs")

    print("  ScrapedData indicators:")
    scraped_sample = db.query(ScrapedData).filter_by(company_id=14, year=2024).limit(10).all()
    scraped_ids = set()
    for i, s in enumerate(scraped_sample):
        scraped_ids.add(s.data_key)
        print(f"    {i+1}. {s.data_key} (source: {s.source})")

    print("  Answer indicators:")
    answer_sample = db.query(Answer).filter_by(company_id=14, year=2024).limit(10).all()
    answer_ids = set()
    for i, a in enumerate(answer_sample):
        answer_ids.add(a.indicator_id)
        print(f"    {i+1}. {a.indicator_id} (source: {a.source})")

    # Step 3: Check ID overlap
    print("\nStep 3: Indicator ID Analysis")
    common_ids = scraped_ids.intersection(answer_ids)
    print(f"  Common IDs between ScrapedData and Answer: {len(common_ids)}")
    if common_ids:
        print(f"  Sample common IDs: {list(common_ids)[:5]}")

    # Step 4: Check TARGET 151 framework
    print("\nStep 4: TARGET 151 Framework Analysis")
    try:
        from backend.questionnaire.questionnaire_data import IMPACTREE_STANDARD_QUESTIONNAIRE

        total_target_151 = len(IMPACTREE_STANDARD_QUESTIONNAIRE)
        print(f"  Total TARGET 151 indicators: {total_target_151}")

        target_151_ids = set(IMPACTREE_STANDARD_QUESTIONNAIRE.keys())

        # Check overlap with our Answer IDs
        answer_all_ids = set([a.indicator_id for a in db.query(Answer).filter_by(company_id=14, year=2024).all()])
        target_overlap = answer_all_ids.intersection(target_151_ids)

        print(f"  Answer IDs that match TARGET 151: {len(target_overlap)}")
        print(f"  Sample TARGET 151 matches: {list(target_overlap)[:10]}")

        # Show first 10 TARGET 151 indicators
        sample_target_151 = list(target_151_ids)[:10]
        print(f"  Sample TARGET 151 IDs: {sample_target_151}")

        # Check what our scraped IDs look like vs TARGET 151
        print(f"\nStep 5: ID Format Comparison")
        print(f"  Our ScrapedData IDs: {list(scraped_ids)[:5]}")
        print(f"  TARGET 151 IDs: {sample_target_151[:5]}")

        # Check if there's a pattern mismatch
        our_format = list(scraped_ids)[0] if scraped_ids else "NONE"
        target_format = sample_target_151[0] if sample_target_151 else "NONE"

        print(f"\\nFormat Analysis:")
        print(f"  Our format example: {our_format}")
        print(f"  TARGET format example: {target_format}")

    except Exception as e:
        print(f"  Could not access TARGET 151: {e}")

    # Step 6: Check source distribution
    print(f"\nStep 6: Source Distribution Analysis")

    scraped_sources = {}
    for s in scraped_sample:
        source = s.source
        scraped_sources[source] = scraped_sources.get(source, 0) + 1

    answer_sources = {}
    for a in answer_sample:
        source = a.source
        answer_sources[source] = answer_sources.get(source, 0) + 1

    print(f"  ScrapedData sources: {scraped_sources}")
    print(f"  Answer sources: {answer_sources}")

    db.close()

    return {
        'scraped_count': scraped_count,
        'answer_count': answer_count,
        'common_ids': len(common_ids) if 'common_ids' in locals() else 0,
        'target_overlap': len(target_overlap) if 'target_overlap' in locals() else 0
    }


def fix_indicator_id_mapping():
    """Fix the indicator ID mapping to align with TARGET 151"""

    print("\n=== FIXING INDICATOR ID MAPPING ===")

    # Load TARGET 151 framework
    try:
        from backend.questionnaire.questionnaire_data import IMPACTREE_STANDARD_QUESTIONNAIRE
        target_151_ids = set(IMPACTREE_STANDARD_QUESTIONNAIRE.keys())
        print(f"Loaded TARGET 151 framework: {len(target_151_ids)} indicators")

        # Create mapping from our IDs to TARGET 151 IDs
        id_mapping = {}

        # Common patterns in our system vs TARGET 151
        our_patterns = [
            'IMP-M01-I01', 'IMP-M01-I02', 'IMP-M01-I03', 'IMP-M01-I04', 'IMP-M01-I05',
            'IMP-M02-I01', 'IMP-M02-I02', 'IMP-M03-I01', 'IMP-M03-I02', 'IMP-M05-I01',
            'IMP-M05-I02', 'IMP-M06-I01', 'IMP-M07-I01', 'IMP-M15-I01', 'IMP-M16-I01'
        ]

        # Check which of our patterns exist in TARGET 151
        matching_patterns = []
        for pattern in our_patterns:
            if pattern in target_151_ids:
                matching_patterns.append(pattern)
                id_mapping[pattern] = pattern  # Direct match

        print(f"Direct pattern matches: {len(matching_patterns)}")
        print(f"Sample matches: {matching_patterns[:5]}")

        return id_mapping

    except Exception as e:
        print(f"Failed to load TARGET 151 framework: {e}")
        return {}


if __name__ == "__main__":
    # Run debugging
    debug_results = debug_indicator_mapping()

    print(f"\n=== SUMMARY ===")
    print(f"ScrapedData records: {debug_results['scraped_count']}")
    print(f"Answer records: {debug_results['answer_count']}")
    print(f"TARGET 151 overlap: {debug_results['target_overlap']}")

    # Try to fix mapping
    mapping = fix_indicator_id_mapping()

    print(f"\n=== FIXES NEEDED ===")
    if debug_results['target_overlap'] < 10:
        print("1. CRITICAL: Fix indicator ID mapping to TARGET 151 format")
        print("2. Update document discovery to use correct TARGET 151 IDs")
        print("3. Verify comprehensive pipeline uses TARGET 151 framework")
    else:
        print("Indicator mapping appears correct - investigate other issues")