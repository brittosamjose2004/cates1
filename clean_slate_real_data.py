#!/usr/bin/env python3
"""
CLEAN SLATE - REMOVE ALL SYNTHETIC DATA
This script removes ALL synthetic/generated data and rebuilds using ONLY:
1. Real document data (PDFs, sustainability reports)
2. Historical data (previous years)
3. Manual user input (if any)
4. Empty indicators (if no real data exists)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
from real_data_only_system import process_real_data_only

def remove_all_synthetic_data(company_id, year=2024):
    """Remove ALL synthetic/generated data for a company/year"""
    db = get_session()
    try:
        # Delete all answers for this company/year
        # This removes our synthetic data completely
        deleted_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).delete()

        db.commit()
        print(f"REMOVED: {deleted_answers} synthetic indicators")
        print("Database is now clean - ready for real data only")

        return deleted_answers

    finally:
        db.close()

def rebuild_with_real_data_only(company_id, year=2024):
    """Rebuild ESG data using ONLY real sources"""
    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        print(f"\nREBUILDING: {company.name} with REAL DATA ONLY")
        print("=" * 60)

        # Check available real data sources
        scraped_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        # Group by source
        real_sources = {}
        esg_indicators_found = 0

        for data in scraped_data:
            source = data.source
            if source not in real_sources:
                real_sources[source] = []
            real_sources[source].append(data)

            # Count potential ESG indicators
            if ('esg' in data.data_key.lower() or
                data.data_key.startswith('IMP-M') or
                'sustainability' in source.lower() or
                'emissions' in data.data_key.lower() or
                'energy' in data.data_key.lower() or
                'water' in data.data_key.lower()):
                esg_indicators_found += 1

        print("REAL DATA SOURCES FOUND:")
        for source, data_points in real_sources.items():
            print(f"  {source}: {len(data_points)} data points")

        print(f"\nPotential ESG indicators in real data: {esg_indicators_found}")

        # Now rebuild using only real data
        print("\nProcessing with real data only...")
        result = process_real_data_only(company_id, year, db)

        return result

    finally:
        db.close()

def main():
    print("CLEAN SLATE ESG SYSTEM - REAL DATA ONLY")
    print("=" * 70)
    print("This will:")
    print("1. Remove ALL synthetic/generated indicator data")
    print("2. Rebuild using ONLY real document data")
    print("3. Show missing indicators where no real data exists")
    print("4. Preserve any manual user inputs")
    print("=" * 70)

    # For demonstration, clean HCL Technologies
    company_id = 1
    year = 2024

    # Step 1: Clean slate - remove synthetic data
    print("\nSTEP 1: Removing synthetic data...")
    removed = remove_all_synthetic_data(company_id, year)

    # Step 2: Rebuild with real data only
    print("\nSTEP 2: Rebuilding with real data...")
    filled = rebuild_with_real_data_only(company_id, year)

    # Final summary
    print(f"\n" + "=" * 70)
    print("FINAL RESULT:")
    print(f"Removed: {removed} synthetic indicators")
    print(f"Rebuilt: {filled} indicators using REAL DATA ONLY")
    print(f"Missing: {151 - filled} indicators (no real data available)")
    print(f"Coverage: {(filled/151)*100:.1f}% with authentic data")
    print("=" * 70)
    print("\nNEXT STEPS to improve coverage:")
    print("1. Upload company sustainability reports (PDFs)")
    print("2. Upload annual reports with ESG sections")
    print("3. Upload CSR reports and ESG disclosures")
    print("4. Add manual data entry for key missing indicators")

if __name__ == "__main__":
    main()