#!/usr/bin/env python3
"""
Enhanced Online Document Fetcher for Real ESG Data
Downloads company documents from online sources and extracts real ESG values
Replaces intelligent defaults with actual document-based data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
import requests
import re
import time
from urllib.parse import urlparse, urljoin
import PyPDF2
import io
from datetime import datetime

def fetch_company_documents_online(company_id, year=2024):
    """Fetch additional company documents from online sources"""

    db = get_session()
    try:
        # Get company info
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"ERROR: Company ID {company_id} not found")
            return

        company_name = company.name
        print("ENHANCED ONLINE DOCUMENT FETCHER")
        print("="*60)
        print(f"Company: {company_name}")
        print(f"Fetching additional ESG documents from online sources")
        print("="*60)

        # 1. Check what indicators need real data (currently have intelligent defaults)
        missing_indicators = find_missing_real_data(company_id, year, db)
        print(f"\nINDICATORS NEEDING REAL DATA: {len(missing_indicators)}")

        if len(missing_indicators) == 0:
            print("All indicators already have real data!")
            return

        # Show sample missing indicators
        for i, indicator_id in enumerate(missing_indicators[:10], 1):
            print(f"   {i:2d}. {indicator_id}")
        if len(missing_indicators) > 10:
            print(f"   ... and {len(missing_indicators) - 10} more")

        # 2. Generate document search URLs
        document_urls = generate_document_search_urls(company_name, company.ticker)
        print(f"\nSEARCHING FOR DOCUMENTS:")

        total_documents_found = 0
        successful_extractions = 0

        # 3. Try to fetch documents
        for doc_type, urls in document_urls.items():
            print(f"\n{doc_type}:")

            for url in urls:
                try:
                    print(f"   Fetching: {url[:60]}...")

                    doc_content = fetch_document_content(url)

                    if doc_content and len(doc_content) > 1000:  # Only process substantial content
                        print(f"     * Downloaded: {len(doc_content)} chars")

                        # Extract ESG data from document
                        extracted_data = extract_esg_from_document_content(doc_content, doc_type)

                        if extracted_data:
                            print(f"     * Extracted: {len(extracted_data)} ESG data points")

                            # Store in database
                            store_extracted_data(company_id, year, doc_type, url, extracted_data, db)
                            successful_extractions += len(extracted_data)
                            total_documents_found += 1

                            # Show sample extractions
                            for key, value in list(extracted_data.items())[:3]:
                                value_preview = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                                print(f"       - {key}: {value_preview}")
                        else:
                            print(f"     * No ESG data found in document")
                    else:
                        print(f"     * Document too small or failed to fetch")

                except Exception as e:
                    print(f"     * Error: {str(e)[:40]}...")
                    continue

                # Rate limiting
                time.sleep(2)

        # 4. Process extracted data and update indicators
        if successful_extractions > 0:
            print(f"\n" + "="*60)
            print("PROCESSING EXTRACTED DATA")
            print("="*60)

            updated_indicators = update_indicators_with_real_data(company_id, year, missing_indicators, db)

            print(f"RESULTS:")
            print(f"   * Documents processed: {total_documents_found}")
            print(f"   * ESG data points extracted: {successful_extractions}")
            print(f"   * Indicators updated with real data: {updated_indicators}")
            print(f"   * Remaining intelligent defaults: {len(missing_indicators) - updated_indicators}")

            return updated_indicators
        else:
            print(f"\nNo additional ESG data found in online documents")
            return 0

    except Exception as e:
        print(f"ERROR during online document fetching: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

def find_missing_real_data(company_id, year, db):
    """Find indicators that currently have intelligent defaults"""

    answers = db.query(Answer).filter_by(
        company_id=company_id,
        year=year,
        source="intelligent_default"
    ).all()

    return [answer.indicator_id for answer in answers]

def generate_document_search_urls(company_name, ticker):
    """Generate URLs to search for company ESG documents"""

    # Clean company name for search
    search_name = re.sub(r'[^\w\s]', '', company_name).strip()
    search_terms = search_name.replace(' ', '+')

    document_urls = {
        'Annual Reports': [
            f"https://www.google.com/search?q={search_terms}+annual+report+2024+filetype:pdf",
            f"https://www.google.com/search?q={search_terms}+annual+report+2023+filetype:pdf",
        ],
        'Sustainability Reports': [
            f"https://www.google.com/search?q={search_terms}+sustainability+report+2024+filetype:pdf",
            f"https://www.google.com/search?q={search_terms}+ESG+report+2024+filetype:pdf",
            f"https://www.google.com/search?q={search_terms}+CSR+report+2024+filetype:pdf",
        ],
        'Company Website': [
            f"https://www.google.com/search?q={search_terms}+investor+relations",
            f"https://www.google.com/search?q={search_terms}+sustainability+ESG",
        ],
        'Stock Exchange Filings': [
            f"https://www.nseindia.com/companies-listing/corporate-filings-company-search?q={search_terms}",
            f"https://www.bseindia.com/corporates/List_Scrips.aspx?expandable=3&q={search_terms}",
        ] if ticker else []
    }

    return document_urls

def fetch_document_content(url):
    """Fetch content from document URL"""

    try:
        # Set up headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()

        if 'pdf' in content_type:
            # Extract text from PDF
            return extract_text_from_pdf(response.content)
        else:
            # HTML content
            return response.text

    except Exception as e:
        return None

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""

    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        return text
    except:
        return None

def extract_esg_from_document_content(content, doc_type):
    """Extract ESG data from document content using advanced patterns"""

    extracted_data = {}
    content_lower = content.lower()

    # Comprehensive ESG extraction patterns
    esg_patterns = {
        # Energy Data
        'energy_consumption_mwh': [
            r'energy consumption[:\s]*([0-9,]+\.?[0-9]*)\s*(mwh|megawatt)',
            r'total energy[:\s]*([0-9,]+\.?[0-9]*)\s*(mwh|megawatt)',
            r'electricity consumption[:\s]*([0-9,]+\.?[0-9]*)\s*(mwh|kwh)',
        ],
        'renewable_energy_percent': [
            r'renewable energy[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
            r'clean energy[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
            r'green energy[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
        ],

        # Emissions Data
        'scope1_emissions': [
            r'scope\s*1\s*emissions?[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?|tonnes?)',
            r'direct emissions?[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?|tonnes?)',
        ],
        'scope2_emissions': [
            r'scope\s*2\s*emissions?[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?|tonnes?)',
            r'indirect emissions?[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?|tonnes?)',
        ],
        'carbon_intensity': [
            r'carbon intensity[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?.*revenue|kg.*unit)',
            r'emissions intensity[:\s]*([0-9,]+\.?[0-9]*)\s*(tco2e?.*revenue)',
        ],

        # Water Management
        'water_consumption': [
            r'water consumption[:\s]*([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|kl|megalit)',
            r'water usage[:\s]*([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|kl|megalit)',
            r'water withdrawal[:\s]*([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|kl|megalit)',
        ],
        'water_recycled': [
            r'water recycl[a-z]*[:\s]*([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|kl|%|percent)',
            r'recycl[a-z]*\s*water[:\s]*([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|kl|%)',
        ],

        # Waste Management
        'waste_generated': [
            r'waste generated?[:\s]*([0-9,]+\.?[0-9]*)\s*(tonnes?|mt|kg)',
            r'total waste[:\s]*([0-9,]+\.?[0-9]*)\s*(tonnes?|mt|kg)',
        ],
        'waste_recycling_rate': [
            r'waste recycl[a-z]*[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
            r'recycl[a-z]*\s*rate[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
        ],

        # Employment & Social
        'total_workforce': [
            r'total workforce[:\s]*([0-9,]+)',
            r'total employees?[:\s]*([0-9,]+)',
            r'headcount[:\s]*([0-9,]+)',
        ],
        'women_workforce': [
            r'women\s*(in\s*)?workforce[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
            r'female employees?[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
        ],
        'training_hours_per_employee': [
            r'training hours?.*employee[:\s]*([0-9,]+\.?[0-9]*)',
            r'average training[:\s]*([0-9,]+\.?[0-9]*)\s*hours?',
        ],

        # Health & Safety
        'lost_time_injury_rate': [
            r'ltifr[:\s]*([0-9,]+\.?[0-9]*)',
            r'lost time injury.*rate[:\s]*([0-9,]+\.?[0-9]*)',
            r'injury frequency[:\s]*([0-9,]+\.?[0-9]*)',
        ],
        'safety_training_hours': [
            r'safety training[:\s]*([0-9,]+\.?[0-9]*)\s*hours?',
            r'health.*safety.*training[:\s]*([0-9,]+\.?[0-9]*)',
        ],

        # Governance & Finance
        'board_independence': [
            r'independent directors?[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
            r'board independence[:\s]*([0-9,]+\.?[0-9]*)\s*(%|percent)',
        ],
        'csr_expenditure': [
            r'csr.*expend[a-z]*[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|million|billion)?',
            r'csr.*spend[a-z]*[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|million|billion)?',
        ],

        # Environmental Certifications
        'iso14001_certification': [
            r'iso\s*14001',
            r'environmental.*management.*system.*certified',
        ],
        'iso45001_certification': [
            r'iso\s*45001',
            r'occupation.*health.*safety.*certified',
        ],
    }

    # Apply patterns
    for data_key, pattern_list in esg_patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, content_lower, re.IGNORECASE)

            for match in matches:
                if len(match.groups()) >= 1:
                    value = match.group(1).replace(',', '')
                    unit = match.group(2) if len(match.groups()) >= 2 else ''

                    # Format the extracted value
                    if value:
                        if data_key.endswith('_certification'):
                            extracted_data[data_key] = "Yes - Certified"
                        else:
                            extracted_data[data_key] = f"{value} {unit}".strip()
                        break  # Use first match

    return extracted_data

def store_extracted_data(company_id, year, doc_type, source_url, extracted_data, db):
    """Store extracted ESG data in database"""

    for data_key, data_value in extracted_data.items():
        # Check if this data already exists
        existing = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year,
            source=f"online_{doc_type}",
            data_key=data_key
        ).first()

        if not existing:
            scraped_record = ScrapedData(
                company_id=company_id,
                year=year,
                source=f"online_{doc_type}",
                data_key=data_key,
                data_value=data_value
            )
            db.add(scraped_record)

    db.commit()

def update_indicators_with_real_data(company_id, year, missing_indicators, db):
    """Update missing indicators with newly extracted real data"""

    # Mapping of extracted data keys to ESG indicators
    data_to_indicator_map = {
        'energy_consumption_mwh': ['IMP-M06-I01', 'IMP-M06-I04'],
        'renewable_energy_percent': ['IMP-M06-I02', 'IMP-M06-I05'],
        'scope1_emissions': ['IMP-M05-I01'],
        'scope2_emissions': ['IMP-M05-I02'],
        'carbon_intensity': ['IMP-M05-I04'],
        'water_consumption': ['IMP-M07-I01', 'IMP-M07-I05'],
        'water_recycled': ['IMP-M07-I03'],
        'waste_generated': ['IMP-M08-I01'],
        'waste_recycling_rate': ['IMP-M08-I02'],
        'total_workforce': ['IMP-M15-I01', 'IMP-M16-I01'],
        'women_workforce': ['IMP-M16-I02'],
        'training_hours_per_employee': ['IMP-M17-I01', 'IMP-M17-I03'],
        'lost_time_injury_rate': ['IMP-M15-I04'],
        'safety_training_hours': ['IMP-M15-I09'],
        'board_independence': ['IMP-M03-I01', 'IMP-M03-I02'],
        'csr_expenditure': ['IMP-M18-I04'],
        'iso14001_certification': ['IMP-M02-I03'],
        'iso45001_certification': ['IMP-M02-I03'],
    }

    # Get newly extracted data
    new_data = db.query(ScrapedData).filter(
        ScrapedData.company_id == company_id,
        ScrapedData.year == year,
        ScrapedData.source.like('online_%')
    ).all()

    updated_count = 0

    for data_record in new_data:
        data_key = data_record.data_key
        data_value = data_record.data_value

        if data_key in data_to_indicator_map:
            for indicator_id in data_to_indicator_map[data_key]:
                if indicator_id in missing_indicators:
                    # Update the indicator with real data
                    answer = db.query(Answer).filter_by(
                        company_id=company_id,
                        year=year,
                        indicator_id=indicator_id
                    ).first()

                    if answer and answer.source == "intelligent_default":
                        answer.answer_value = data_value
                        answer.source = f"scraped_{data_record.source}"
                        answer.confidence = 0.95
                        answer.notes = f"Real data extracted from online documents: {data_key}"
                        updated_count += 1

    db.commit()
    return updated_count

def test_online_document_fetching(company_id):
    """Test the online document fetching system"""

    print("TESTING ONLINE DOCUMENT FETCHING")
    print("="*50)

    updated_indicators = fetch_company_documents_online(company_id, 2024)

    if updated_indicators > 0:
        print(f"\nSUCCESS: Updated {updated_indicators} indicators with real online data!")

        # Show results
        from backend.api.routers.indicators import get_indicator_summary
        db = get_session()
        try:
            summary = get_indicator_summary(company_id, 2024, db)
            overall = summary['overall_summary']

            print(f"NEW COVERAGE: {overall['completion_rate']:.1f}%")
            print(f"INDICATORS: {overall['indicators_with_values']}/151")
            print("SOURCE: Mix of real scraped + online extracted data")
        finally:
            db.close()
    else:
        print("No additional real data found online")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--company_id", type=int, required=True, help="Company ID to fetch documents for")

    args = parser.parse_args()

    test_online_document_fetching(args.company_id)