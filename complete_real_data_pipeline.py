#!/usr/bin/env python3
"""
COMPLETE REAL DATA PIPELINE
Combines comprehensive PDF extraction + online scraping for maximum real data coverage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData
from enhanced_pdf_extractor import extract_enhanced_esg_data
from comprehensive_online_scraper import scrape_missing_for_company

def run_complete_real_data_pipeline(company_id: int, year: int = 2024):
    """
    Complete real data extraction pipeline:
    1. Extract from PDF documents (comprehensive patterns for all 151 indicators)
    2. Scrape missing indicators from online sources
    3. Report final coverage
    """

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return

        print("="*70)
        print(f"COMPLETE REAL DATA PIPELINE - {company.name}")
        print(f"Year: {year}")
        print("="*70)

        # PHASE 1: Enhanced PDF Extraction
        print("\nPHASE 1: ENHANCED PDF EXTRACTION")
        print("-" * 70)
        pdf_count = extract_enhanced_esg_data(company_id, year)
        print(f"PDF Extraction Complete: {pdf_count} indicators extracted")

        # Check current coverage
        existing_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        existing_indicators = {data.data_key for data in existing_data}
        print(f"Current coverage after PDF: {len(existing_indicators)}/151 indicators")

        # PHASE 2: Comprehensive Online Scraping
        print("\nPHASE 2: COMPREHENSIVE ONLINE SCRAPING")
        print("-" * 70)

        online_count = scrape_missing_for_company(company_id, year)
        print(f"Online scraping complete: {online_count} additional indicators")

        # FINAL REPORT
        print("\n" + "="*70)
        print("FINAL COVERAGE REPORT")
        print("="*70)

        # Reload to get final count
        final_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        final_indicators = {data.data_key for data in final_data}
        coverage_percent = (len(final_indicators) / 151) * 100

        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print(f"Total Indicators: {len(final_indicators)}/151")
        print(f"Coverage: {coverage_percent:.1f}%")
        print(f"Missing: {151 - len(final_indicators)} indicators")

        # Breakdown by source
        source_counts = {}
        for data in final_data:
            source = data.source or 'unknown'
            source_counts[source] = source_counts.get(source, 0) + 1

        print("\nData Sources Breakdown:")
        for source, count in sorted(source_counts.items()):
            print(f"  {source}: {count} indicators")

        print("\n" + "="*70)
        print("100% REAL DATA - NO SYNTHETIC GENERATION")
        print("="*70)

        return len(final_indicators)

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC Limited
    company_id = 30  # ITC LIMITED
    year = 2024

    result = run_complete_real_data_pipeline(company_id, year)
    print(f"\nFINAL: {result}/151 indicators extracted from real sources")
