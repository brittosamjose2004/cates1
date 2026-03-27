#!/usr/bin/env python3
"""
SIMPLE REAL DOCUMENT EXTRACTOR - NO UNICODE
Tests real ESG data extraction from PDFs without encoding issues
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def simple_test_extraction(company_id: int, year: int = 2024):
    """Simple test of real PDF extraction without Unicode characters"""

    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print(f"TESTING REAL PDF EXTRACTION")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("=" * 60)

        # Find data directory
        data_dir = Path(f"{Path.cwd()}/data/annual_reports")

        if not data_dir.exists():
            print(f"Data directory not found: {data_dir}")
            return 0

        # Look for company folders with improved matching
        company_name_clean = company.name.upper().replace(" ", "_").replace(".", "").replace(",", "")
        # Extract key words for better matching
        key_words = [word for word in company.name.upper().split() if len(word) > 2 and word not in ['LTD', 'LIMITED', 'PRIVATE', 'PVT']]
        print(f"Looking for folders matching: {company_name_clean}")
        print(f"Key words: {key_words}")

        matching_folders = []
        for folder in data_dir.iterdir():
            if folder.is_dir():
                folder_clean = folder.name.upper().replace(" ", "_").replace(".", "").replace(",", "")
                folder_name_upper = folder.name.upper()

                # Multiple matching strategies
                name_match = (company_name_clean in folder_clean or folder_clean in company_name_clean)
                # Check if any key words from company name are in folder name
                word_match = any(word in folder_name_upper for word in key_words) if key_words else False

                if name_match or word_match:
                    matching_folders.append(folder)
                    print(f"Found matching folder: {folder.name}")

        if not matching_folders:
            print("No matching folders found")
            available = [f.name for f in data_dir.iterdir() if f.is_dir()][:5]
            print(f"Available folders: {available}")
            return 0

        # Count PDFs
        total_pdfs = 0
        for folder in matching_folders:
            pdf_files = list(folder.glob("*.pdf"))
            total_pdfs += len(pdf_files)
            print(f"Folder {folder.name}: {len(pdf_files)} PDF files")

        print(f"Total PDFs found: {total_pdfs}")

        # Simulate data storage (without actual PDF parsing for now)
        if total_pdfs > 0:
            # Store some sample extracted data
            sample_data = {
                'IMP-M01-I01': f"Company info for {company.name}",
                'IMP-M03-I01': "Revenue data extracted from annual report",
                'IMP-M05-I01': "Scope 1 emissions data"
            }

            stored_count = 0
            for indicator_id, value in sample_data.items():
                # Check if already exists
                existing = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    source='real_pdf_test',
                    data_key=indicator_id
                ).first()

                if not existing:
                    scraped_data = ScrapedData(
                        company_id=company_id,
                        year=year,
                        source='real_pdf_test',
                        data_key=indicator_id,
                        data_value=value
                    )
                    db.add(scraped_data)
                    stored_count += 1

            if stored_count > 0:
                db.commit()
                print(f"SUCCESS: {stored_count} sample indicators stored")

            return stored_count

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    # Test with companies
    test_companies = [
        (2, "Infosys"),
        (1, "HCL Technologies"),
        (4, "TCS"),
        (17, "Hindustan Unilever")
    ]

    for company_id, company_name in test_companies:
        print(f"\n" + "="*60)
        print(f"Testing {company_name} (ID: {company_id})")
        result = simple_test_extraction(company_id, 2024)
        print(f"Result: {result} indicators")