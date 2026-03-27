#!/usr/bin/env python3
"""
Run ESG pipeline specifically for the COMPREHENSIVE ESG TEST COMPANY
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.company_year_processor import CompanyYearProcessor
from backend.database.db import get_session
from backend.database.models import Company

def run_test_company_pipeline():
    """Run ESG pipeline for the comprehensive test company"""
    company_id = 37  # COMPREHENSIVE ESG TEST COMPANY
    year = 2024

    db = get_session()
    try:
        # Verify company exists
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"ERROR: Company ID {company_id} not found")
            return

        print("="*80)
        print(f"RUNNING ESG PIPELINE FOR TEST COMPANY")
        print(f"Company: {company.name}")
        print(f"Company ID: {company_id}")
        print(f"Year: {year}")
        print("="*80)

        # Create and run processor
        processor = CompanyYearProcessor(
            company_id=str(company_id),
            year=year,
            standards=["BRSR", "CDP", "EcoVadis", "GRI"]
        )

        # Process with our existing test data (should preserve it)
        result = processor.process_company_year(
            force_refresh=False,  # Don't force refresh to preserve test data
            include_real_time=True,
            trigger_scoring=True
        )

        print(f"\nPIPELINE RESULTS:")
        print(f"   Company ID: {result.company_id}")
        print(f"   Year: {result.year}")
        print(f"   Total Indicators: {result.total_indicators}")
        print(f"   Processed Indicators: {result.processed_indicators}")
        print(f"   Failed Indicators: {result.failed_indicators}")
        print(f"   Modules Processed: {len(result.modules_processed)}")
        print(f"   Processing Time: {result.processing_time_seconds:.2f}s")

        if result.final_score is not None:
            print(f"   Final ESG Score: {result.final_score:.1f}")

        if result.processed_indicators >= 150:  # Should be 151 but allowing small margin
            print(f"\nSUCCESS: Pipeline completed successfully!")
            print(f"   All {result.processed_indicators} indicators are now available in the frontend")
            print(f"   ESG Score: {result.final_score:.1f}" if result.final_score else "")
        else:
            print(f"\nPARTIAL SUCCESS: {result.processed_indicators}/{result.total_indicators} indicators processed")

        if result.errors:
            print(f"\nERRORS:")
            for error in result.errors:
                print(f"   - {error}")

        print(f"\nNOTE: The pipeline processed {result.processed_indicators} indicators.")
        print(f"Our test data has 151 indicators. This discrepancy suggests the")
        print(f"CompanyYearProcessor may be using a different indicator set.")

        return result

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    run_test_company_pipeline()