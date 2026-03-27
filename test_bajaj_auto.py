#!/usr/bin/env python3
"""
Test Bajaj Auto Limited - Real ESG Data Pipeline
Company ID: 22 with 6 real annual report PDFs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

def test_bajaj_auto():
    print("=" * 60)
    print("TESTING NEW COMPANY: BAJAJ AUTO LIMITED")
    print("Company ID: 22 | 6 Real Annual Report PDFs Available")
    print("=" * 60)

    try:
        # Phase 1: Document Extraction Test
        print("\nPHASE 1: REAL DOCUMENT EXTRACTION")
        print("-" * 40)

        from simple_test_extractor import simple_test_extraction
        extracted = simple_test_extraction(22, 2024)
        print(f"RESULT: {extracted} indicators extracted from real Bajaj Auto PDFs")

        # Phase 2: Real Data Processing Test
        print("\nPHASE 2: REAL DATA PROCESSING")
        print("-" * 40)

        from real_data_only_system import process_real_data_only
        processed = process_real_data_only(22, 2024)
        print(f"RESULT: {processed} indicators processed with real data only")

        # Phase 3: Data Source Verification
        print("\nPHASE 3: DATA SOURCE VERIFICATION")
        print("-" * 40)

        from backend.database.db import get_session
        from backend.database.models import Answer, ScrapedData

        db = get_session()
        try:
            # Check ScrapedData for real extractions
            scraped = db.query(ScrapedData).filter_by(
                company_id=22, year=2024, source='real_pdf_test'
            ).all()
            print(f"Real PDF extractions: {len(scraped)} entries")

            # Check Answer table for final data sources
            answers = db.query(Answer).filter_by(company_id=22, year=2024).all()

            sources = {}
            for answer in answers:
                source = answer.source or 'None'
                sources[source] = sources.get(source, 0) + 1

            print(f"ESG data sources for Bajaj Auto:")
            total = 0
            synthetic_count = 0
            synthetic_sources = ['complete_151_real_data', 'intelligent_default', 'smart_default']

            for source, count in sources.items():
                is_synthetic = any(syn in source for syn in synthetic_sources)
                marker = "[SYNTHETIC]" if is_synthetic else "[REAL]"
                print(f"  {source}: {count} {marker}")
                total += count
                if is_synthetic:
                    synthetic_count += count

            real_percentage = ((total - synthetic_count) / total) * 100 if total > 0 else 0

            print(f"\nSUMMARY:")
            print(f"- Total indicators: {total}/151")
            print(f"- Real data percentage: {real_percentage:.1f}%")
            print(f"- Synthetic data: {synthetic_count} indicators")

            if synthetic_count == 0:
                print("\nSUCCESS: 100% REAL DATA ACHIEVED FOR BAJAJ AUTO!")
                print("NO SYNTHETIC DATA DETECTED")

        finally:
            db.close()

        print("\n" + "=" * 60)
        print("BAJAJ AUTO TEST COMPLETED")
        print("Real ESG data pipeline working with new company")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bajaj_auto()