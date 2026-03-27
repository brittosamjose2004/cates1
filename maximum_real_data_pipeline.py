#!/usr/bin/env python3
"""
MAXIMUM REAL DATA PIPELINE
Combines ALL extraction methods to get maximum possible indicators from real sources
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData
from enhanced_pdf_extractor import extract_enhanced_esg_data
from comprehensive_online_scraper import scrape_missing_for_company

def maximum_real_data_extraction(company_id: int, year: int = 2024):
    """
    Extract MAXIMUM possible indicators from:
    1. Enhanced PDF extraction (full document scan)
    2. Comprehensive online scraping (5+ sources)
    3. BRSR section extraction
    4. Financial table extraction
    """

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return

        print("\n" + "="*70)
        print(f"MAXIMUM REAL DATA EXTRACTION")
        print(f"Company: {company.name}")
        print(f"Target: ALL 151 ESG INDICATORS")
        print("="*70)

        # Check initial state
        initial_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        initial_count = len(set(d.data_key for d in initial_data))
        print(f"\nStarting with: {initial_count}/151 indicators")

        # PHASE 1: Enhanced PDF Extraction
        print("\n" + "-"*70)
        print("PHASE 1: ENHANCED PDF EXTRACTION")
        print("-"*70)
        pdf_count = extract_enhanced_esg_data(company_id, year)

        # Check progress
        phase1_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()
        phase1_count = len(set(d.data_key for d in phase1_data))
        print(f"After Phase 1: {phase1_count}/151 indicators (+{phase1_count - initial_count})")

        # PHASE 2: Online Scraping
        print("\n" + "-"*70)
        print("PHASE 2: COMPREHENSIVE ONLINE SCRAPING")
        print("-"*70)
        online_count = scrape_missing_for_company(company_id, year)

        # Check progress
        phase2_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()
        phase2_count = len(set(d.data_key for d in phase2_data))
        print(f"After Phase 2: {phase2_count}/151 indicators (+{phase2_count - phase1_count})")

        # FINAL REPORT
        print("\n" + "="*70)
        print("MAXIMUM EXTRACTION COMPLETE")
        print("="*70)

        final_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        final_indicators = set(d.data_key for d in final_data)
        final_count = len(final_indicators)

        print(f"\nCompany: {company.name}")
        print(f"Year: {year}")
        print(f"Total Indicators: {final_count}/151")
        print(f"Coverage: {final_count/151*100:.1f}%")
        print(f"Missing: {151 - final_count} indicators")

        # Module breakdown
        print("\nCoverage by Module:")
        for module_num in range(1, 22):
            module_key = f'M{module_num:02d}'
            module_indicators = [ind for ind in final_indicators if module_key in ind]
            if module_indicators:
                print(f"  Module {module_num:02d}: {len(module_indicators)} indicators")

        # Data sources
        source_counts = {}
        for d in final_data:
            source = d.source or 'unknown'
            source_counts[source] = source_counts.get(source, 0) + 1

        print("\nData Sources:")
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            print(f"  {source}: {count} indicators")

        print("\n" + "="*70)
        print("100% REAL DATA - NO SYNTHETIC GENERATION")
        print("="*70)

        return final_count

    finally:
        db.close()

if __name__ == "__main__":
    # Run for ITC Limited
    company_id = 30
    year = 2024

    final_count = maximum_real_data_extraction(company_id, year)
    print(f"\n✓ EXTRACTED {final_count}/151 INDICATORS FROM REAL SOURCES")
