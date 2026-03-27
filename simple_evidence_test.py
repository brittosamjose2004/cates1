#!/usr/bin/env python3
"""
Simple Evidence Processing Test
Tests the evidence processing workflow without Unicode characters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, EvidenceSource
from backend.services.evidence_processor import extract_industry_specific_indicators, fill_indicator_gaps

def test_extraction_system():
    """Test the extraction system components."""

    print("="*60)
    print("EVIDENCE PROCESSING TEST")
    print("="*60)

    db = get_session()

    try:
        # Get or create test company
        company = db.query(Company).first()
        if not company:
            print("No companies found in database")
            return

        print(f"Testing with company: {company.name}")
        print(f"Industry: {company.industry or 'Unknown'}")

        # Generate all 151 indicators
        all_indicators = [f"IMP-M{m:02d}-I{i:02d}" for m in range(1, 22) for i in range(1, 20)][:151]
        print(f"Total indicators to extract: {len(all_indicators)}")

        # Test industry-specific extraction
        print("\nTesting industry-specific patterns...")
        industry_data = extract_industry_specific_indicators("mock.pdf", all_indicators, company)
        print(f"Industry patterns found: {len(industry_data)} indicators")

        # Test gap filling
        remaining = [ind for ind in all_indicators if ind not in industry_data]
        print(f"Remaining indicators: {len(remaining)}")

        print("Testing gap filling...")
        gap_data = fill_indicator_gaps(remaining, company, industry_data)
        print(f"Gap filling found: {len(gap_data)} indicators")

        # Calculate totals
        total = len(industry_data) + len(gap_data)
        coverage = (total / 151) * 100

        print(f"\nRESULTS:")
        print(f"Industry-specific: {len(industry_data)}")
        print(f"Gap filling: {len(gap_data)}")
        print(f"Total extracted: {total}/151")
        print(f"Coverage: {coverage:.1f}%")

        # Show sample data
        print(f"\nSample industry indicators:")
        count = 0
        for key, value in industry_data.items():
            if count >= 5:
                break
            print(f"  {key}: {value}")
            count += 1

        print(f"\nSample gap-filled indicators:")
        count = 0
        for key, value in gap_data.items():
            if count >= 5:
                break
            print(f"  {key}: {value}")
            count += 1

        if total >= 100:
            print(f"\nSUCCESS: Extraction system operational!")
            print(f"Ready for Evidence Locker integration")
        else:
            print(f"\nWARNING: Lower than expected coverage")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_extraction_system()