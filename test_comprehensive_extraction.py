#!/usr/bin/env python3
"""
TEST COMPREHENSIVE EXTRACTION
Quick test of the comprehensive extraction system without timeouts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def test_data_availability():
    """Test what data is available for different companies"""
    db = get_session()
    try:
        # Test a few companies to see what data we have
        companies_to_test = [1, 2, 4, 14, 44]  # HCL, Infosys, TCS, Asian Paints, JSW Steel

        for company_id in companies_to_test:
            company = db.query(Company).filter_by(id=company_id).first()
            if company:
                # Check existing scraped data
                existing_data = db.query(ScrapedData).filter_by(company_id=company_id).count()
                print(f"Company {company_id} ({company.name}): {existing_data} existing data points")

                # Test years with data
                years_with_data = db.query(ScrapedData.year).filter_by(company_id=company_id).distinct().all()
                years = [y[0] for y in years_with_data if y[0]]
                print(f"  Years with data: {years}")

                print()
            else:
                print(f"Company {company_id}: NOT FOUND")

    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
    finally:
        db.close()

def test_simple_extraction(company_id: int = 44, year: int = 2023):
    """Test simple extraction without web scraping"""
    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"[ERROR] Company {company_id} not found")
            return 0

        print(f"[TEST] Testing simple extraction")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("Source: Local data only (no web scraping)")
        print("=" * 60)

        # Check if we have any local PDF data
        from pathlib import Path
        data_dir = Path("data")

        if data_dir.exists():
            # Look for company folders
            annual_reports_dir = data_dir / "annual_reports"
            if annual_reports_dir.exists():
                print(f"[LOCAL] Checking for local PDF data...")

                # Try to find company folder
                company_folders = []
                clean_name = company.name.upper().replace(" ", "_").replace(".", "").replace(",", "")

                for folder in annual_reports_dir.iterdir():
                    if folder.is_dir():
                        folder_clean = folder.name.upper().replace(" ", "_").replace(".", "").replace(",", "")
                        if clean_name in folder_clean or folder_clean in clean_name:
                            company_folders.append(folder)

                print(f"[LOCAL] Found {len(company_folders)} matching folders")
                for folder in company_folders:
                    pdf_files = list(folder.glob("*.pdf"))
                    print(f"  {folder.name}: {len(pdf_files)} PDF files")

            else:
                print(f"[LOCAL] No annual_reports directory found")
        else:
            print(f"[LOCAL] No data directory found")

        # Check existing database data
        existing_data = db.query(ScrapedData).filter_by(company_id=company_id, year=year).all()
        print(f"[DATABASE] Found {len(existing_data)} existing indicators for {year}")

        if existing_data:
            # Group by source
            by_source = {}
            for data in existing_data:
                source = data.source if hasattr(data, 'source') else "unknown"
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(data.data_key if hasattr(data, 'data_key') else data.key)

            print("[DATABASE] Data by source:")
            for source, indicators in by_source.items():
                print(f"  {source}: {len(indicators)} indicators")

        return len(existing_data)

    except Exception as e:
        print(f"[ERROR] Simple extraction test failed: {e}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("[START] TESTING COMPREHENSIVE EXTRACTION SYSTEM")
    print("=" * 80)

    # Test 1: Check data availability
    print("TEST 1: Data Availability Check")
    print("-" * 40)
    test_data_availability()

    # Test 2: Simple extraction test
    print("TEST 2: Simple Extraction Test")
    print("-" * 40)
    count = test_simple_extraction(44, 2023)  # JSW Steel 2023
    print(f"\nResult: {count} indicators available")

    print("\n[COMPLETE] Testing finished - no web scraping performed")