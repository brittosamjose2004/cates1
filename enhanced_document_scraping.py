#!/usr/bin/env python3
"""
Enhanced Document-Based ESG Data Extraction
ONLY uses real scraped data from company documents - NO intelligent defaults
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, QuestionnaireSession, ScrapedData
from backend.services.company_year_processor import CompanyYearProcessor
from backend.processor.data_mapper import DataMapper
import re
import json
from datetime import datetime

def enhance_document_scraping(company_id, year=2024):
    """Enhanced scraping to extract MORE real ESG data from company documents"""

    db = get_session()
    try:
        print("ENHANCED DOCUMENT-BASED ESG EXTRACTION")
        print("="*60)
        print(f"Company ID: {company_id} | Year: {year}")
        print("ONLY extracting REAL data from company documents")
        print("NO artificial/intelligent defaults used")
        print("="*60)

        # 1. Get company info
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"ERROR: Company ID {company_id} not found")
            return

        print(f"Company: {company.name}")

        # 2. Get all scraped data key-value pairs for this company
        scraped_data_records = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"Scraped data records found: {len(scraped_data_records)}")

        if not scraped_data_records:
            print("WARNING: No scraped data found for this company!")
            print("Need to process company data first")
            return

        # 3. Show what data is available
        print(f"\nAVAILABLE SCRAPED DATA:")

        # Group data by source
        sources = {}
        for record in scraped_data_records:
            source = record.source
            if source not in sources:
                sources[source] = []
            sources[source].append(record)

        for source, records in sources.items():
            print(f"   {source}: {len(records)} data points")

        # 4. Extract ESG data from scraped key-value pairs
        print(f"\nEXTRACTING ESG DATA:")
        extracted_indicators = extract_esg_from_scraped_data(scraped_data_records)

        total_extracted = len(extracted_indicators)
        print(f"   Real ESG indicators extracted: {total_extracted}")

        # Show sample extracted data
        sample_count = 0
        for indicator_id, data in extracted_indicators.items():
            if sample_count < 5:
                value_preview = str(data['value'])[:50] + "..." if len(str(data['value'])) > 50 else str(data['value'])
                print(f"     * {indicator_id}: {value_preview} (from {data['source']})")
                sample_count += 1

        # 5. Update database with real scraped data
        if total_extracted > 0:
            updated_count = update_database_with_scraped_indicators(
                company_id, year, extracted_indicators, db
            )
            print(f"   Database updated: {updated_count} indicators with real data")

        return total_extracted

    except Exception as e:
        print(f"ERROR during enhanced extraction: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

def extract_esg_from_scraped_data(scraped_records):
    """Extract ESG indicators from scraped key-value data"""

    # Mapping of scraped data keys to ESG indicators
    key_to_indicator_mapping = {
        # Financial Data
        'Total Revenue': 'IMP-M20-I01',
        'Net Revenue': 'IMP-M20-I01',
        'Revenue': 'IMP-M20-I01',
        'Gross Profit': 'IMP-M20-I01',
        'Net profit (CSR 2% basis)': 'IMP-M18-I04',
        'CSR spend': 'IMP-M18-I04',
        'Tax expense': 'IMP-M03-I06',
        'Income tax': 'IMP-M03-I06',
        'Effective tax rate': 'IMP-M03-I06',

        # Employee Data
        'SG&A (includes employee costs)': 'IMP-M14-I03',
        'Employee costs': 'IMP-M14-I03',
        'Total employees': 'IMP-M15-I01',
        'Workforce': 'IMP-M15-I01',
        'Headcount': 'IMP-M15-I01',

        # Company Info
        'Year of incorporation': 'IMP-M01-I01',
        'Incorporation year': 'IMP-M01-I01',
        'Operational presence': 'IMP-M01-I03',
        'Countries of operation': 'IMP-M01-I03',
        'Business sector': 'IMP-M01-I02',
        'Primary business': 'IMP-M01-I02',

        # Debt and Financial Health
        'Total debt': 'IMP-M01-I05',
        'Net debt': 'IMP-M01-I05',
        'Debt to equity': 'IMP-M01-I05',

        # Environmental (if available)
        'Carbon emissions': 'IMP-M05-I01',
        'Energy consumption': 'IMP-M06-I01',
        'Water consumption': 'IMP-M07-I01',
        'Waste generated': 'IMP-M08-I01',

        # Certifications
        'ISO 14001': 'IMP-M02-I03',
        'ISO 9001': 'IMP-M02-I03',
        'ISO 45001': 'IMP-M02-I03',
        'Environmental certifications': 'IMP-M02-I03',

        # Governance
        'Listing exchange': 'IMP-M01-I04',
        'Stock exchange': 'IMP-M01-I04',
        'Reporting currency': 'IMP-M01-I04',
        'Market capitalization': 'IMP-M20-I01',
        'Market cap': 'IMP-M20-I01',
    }

    extracted_indicators = {}

    for record in scraped_records:
        data_key = record.data_key
        data_value = record.data_value
        source = record.source

        # Direct key mapping
        if data_key in key_to_indicator_mapping:
            indicator_id = key_to_indicator_mapping[data_key]
            extracted_indicators[indicator_id] = {
                'value': data_value,
                'source': f'scraped_{source}',
                'data_key': data_key
            }

        # Pattern-based matching for partial key matches
        else:
            # Check for partial matches
            data_key_lower = data_key.lower()

            if any(term in data_key_lower for term in ['revenue', 'turnover', 'sales']):
                extracted_indicators['IMP-M20-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['tax', 'taxation']):
                extracted_indicators['IMP-M03-I06'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['employee', 'workforce', 'staff']):
                extracted_indicators['IMP-M15-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['csr', 'social responsibility']):
                extracted_indicators['IMP-M18-I04'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['debt', 'borrowing']):
                extracted_indicators['IMP-M01-I05'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['energy', 'power', 'electricity']):
                extracted_indicators['IMP-M06-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['emission', 'carbon', 'ghg']):
                extracted_indicators['IMP-M05-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['water', 'h2o']):
                extracted_indicators['IMP-M07-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }
            elif any(term in data_key_lower for term in ['waste', 'disposal']):
                extracted_indicators['IMP-M08-I01'] = {
                    'value': data_value,
                    'source': f'scraped_{source}',
                    'data_key': data_key
                }

    return extracted_indicators

def update_database_with_scraped_indicators(company_id, year, extracted_indicators, db):
    """Update database with real scraped indicator data"""

    updated_count = 0

    # Get or create session
    session = db.query(QuestionnaireSession).filter_by(
        company_id=company_id,
        year=year
    ).first()

    if not session:
        session = QuestionnaireSession(
            company_id=company_id,
            year=year,
            standard="ALL",
            status="in_progress",
            total_questions=151,
            answered_questions=0
        )
        db.add(session)
        db.flush()

    # Update indicators with real scraped data
    for indicator_id, data in extracted_indicators.items():
        existing_answer = db.query(Answer).filter_by(
            company_id=company_id,
            year=year,
            indicator_id=indicator_id
        ).first()

        if existing_answer:
            # Update existing with real scraped data (preserve if manual)
            if existing_answer.source != "manual":
                existing_answer.answer_value = data['value']
                existing_answer.source = data['source']
                existing_answer.confidence = 0.95  # High confidence for real scraped data
                existing_answer.notes = f"Real scraped data: {data['data_key']}"
                updated_count += 1
        else:
            # Create new with real scraped data
            new_answer = Answer(
                session_id=session.id,
                company_id=company_id,
                year=year,
                indicator_id=indicator_id,
                module=get_module_name(indicator_id),
                indicator_name=f"ESG Indicator {indicator_id}",
                answer_value=data['value'],
                source=data['source'],
                confidence=0.95,
                notes=f"Real scraped data: {data['data_key']}"
            )
            db.add(new_answer)
            updated_count += 1

    # Update session
    session.answered_questions = db.query(Answer).filter_by(
        company_id=company_id,
        year=year
    ).count()

    db.commit()
    return updated_count
    """Create comprehensive patterns to extract ESG data from documents"""

    patterns = {
        # Energy & Emissions
        'total_energy_consumption': [
            r'total energy consumption[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh|gj)',
            r'energy consumption[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh)',
            r'consumed[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh|units)',
        ],
        'renewable_energy': [
            r'renewable energy[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh|%)',
            r'solar energy[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh)',
            r'wind energy[:\s]+([0-9,]+\.?[0-9]*)\s*(mwh|kwh)',
        ],
        'ghg_scope1_emissions': [
            r'scope\s*1\s*emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2|tonnes?)',
            r'direct emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2)',
        ],
        'ghg_scope2_emissions': [
            r'scope\s*2\s*emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2|tonnes?)',
            r'indirect emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2)',
        ],
        'total_emissions': [
            r'total.*emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2|tonnes?)',
            r'carbon emissions[:\s]+([0-9,]+\.?[0-9]*)\s*(tco2e|tco2)',
        ],

        # Water Management
        'water_consumption': [
            r'water consumption[:\s]+([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|m3|kl|liters?)',
            r'water usage[:\s]+([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|m3|kl)',
            r'total water[:\s]+([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|m3|kl)',
        ],
        'water_recycled': [
            r'water recycled[:\s]+([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|m3|kl|%)',
            r'recycled.*water[:\s]+([0-9,]+\.?[0-9]*)\s*(cubic\s*meters?|m3|%)',
        ],

        # Waste Management
        'waste_generated': [
            r'waste generated[:\s]+([0-9,]+\.?[0-9]*)\s*(tonnes?|kg|mt)',
            r'total waste[:\s]+([0-9,]+\.?[0-9]*)\s*(tonnes?|kg|mt)',
        ],
        'waste_recycled': [
            r'waste recycled[:\s]+([0-9,]+\.?[0-9]*)\s*(tonnes?|kg|mt|%)',
            r'recycled.*waste[:\s]+([0-9,]+\.?[0-9]*)\s*(tonnes?|%)',
        ],

        # Financial ESG Data
        'revenue': [
            r'total revenue[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|billion|b|million|m)?',
            r'net revenue[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|billion|b)',
            r'turnover[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|billion|b)',
        ],
        'csr_spend': [
            r'csr.*spend[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|million|m)?',
            r'csr.*expenditure[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|million)',
        ],
        'tax_paid': [
            r'tax.*paid[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|billion|b)',
            r'income tax[:\s]+(?:inr|rs\.?|₹)?\s*([0-9,]+\.?[0-9]*)\s*(crore|billion)',
        ],

        # Employment
        'total_employees': [
            r'total employees[:\s]+([0-9,]+)',
            r'workforce[:\s]+([0-9,]+)',
            r'headcount[:\s]+([0-9,]+)',
        ],
        'women_employees': [
            r'women employees[:\s]+([0-9,]+\.?[0-9]*)\s*(%)?',
            r'female.*workforce[:\s]+([0-9,]+\.?[0-9]*)\s*(%)?',
        ],
        'training_hours': [
            r'training hours[:\s]+([0-9,]+\.?[0-9]*)',
            r'learning.*hours[:\s]+([0-9,]+\.?[0-9]*)',
        ],

        # Safety
        'safety_incidents': [
            r'safety incidents[:\s]+([0-9,]+)',
            r'accidents[:\s]+([0-9,]+)',
            r'ltifr[:\s]+([0-9,]+\.?[0-9]*)',
        ],

        # Certifications & Policies
        'iso_certifications': [
            r'(iso\s*14001|iso\s*45001|iso\s*9001)',
            r'(iso.*certified)',
        ],
        'sustainability_policy': [
            r'(sustainability policy|environmental policy)',
            r'(esg policy|green policy)',
        ],
    }

    return patterns

def apply_enhanced_extraction(text, patterns):
    """Apply extraction patterns to document text"""

    extracted_data = {}
    text_lower = text.lower()

    for data_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)

            for match in matches:
                if len(match.groups()) >= 1:
                    value = match.group(1).replace(',', '')
                    unit = match.group(2) if len(match.groups()) >= 2 else ''

                    # Clean and format the extracted value
                    clean_value = f"{value} {unit}".strip()
                    extracted_data[data_type] = clean_value
                    break  # Use first match found

    return extracted_data

def map_to_esg_indicators(extraction_results):
    """Map extracted data to specific ESG indicator IDs"""

    # Mapping extracted data types to ESG indicators
    indicator_mapping = {
        'total_energy_consumption': ['IMP-M06-I01', 'IMP-M06-I04'],
        'renewable_energy': ['IMP-M06-I02', 'IMP-M06-I05'],
        'ghg_scope1_emissions': ['IMP-M05-I01'],
        'ghg_scope2_emissions': ['IMP-M05-I02'],
        'total_emissions': ['IMP-M05-I01', 'IMP-M05-I02'],
        'water_consumption': ['IMP-M07-I01', 'IMP-M07-I05'],
        'water_recycled': ['IMP-M07-I03'],
        'waste_generated': ['IMP-M08-I01'],
        'waste_recycled': ['IMP-M08-I02'],
        'revenue': ['IMP-M20-I01', 'IMP-M14-I01'],
        'csr_spend': ['IMP-M18-I04'],
        'tax_paid': ['IMP-M03-I06'],
        'total_employees': ['IMP-M15-I01', 'IMP-M16-I01'],
        'women_employees': ['IMP-M16-I02'],
        'training_hours': ['IMP-M17-I01'],
        'safety_incidents': ['IMP-M15-I05'],
        'iso_certifications': ['IMP-M02-I03'],
        'sustainability_policy': ['IMP-M02-I01'],
    }

    mapped_indicators = {}

    # Combine all extracted data from all documents
    all_extracted = {}
    for doc_file, doc_data in extraction_results.items():
        all_extracted.update(doc_data)

    # Map to specific indicators
    for data_type, value in all_extracted.items():
        if data_type in indicator_mapping:
            for indicator_id in indicator_mapping[data_type]:
                mapped_indicators[indicator_id] = {
                    'value': value,
                    'source': 'enhanced_scraped',
                    'data_type': data_type
                }

    return mapped_indicators

def update_database_with_real_data(company_id, year, mapped_indicators, db):
    """Update database with ONLY real scraped data"""

    updated_count = 0

    # Get or create session
    session = db.query(QuestionnaireSession).filter_by(
        company_id=company_id,
        year=year
    ).first()

    if not session:
        session = QuestionnaireSession(
            company_id=company_id,
            year=year,
            standard="ALL",
            status="in_progress",
            total_questions=151,
            answered_questions=0
        )
        db.add(session)
        db.flush()

    # Update only indicators with real scraped data
    for indicator_id, data in mapped_indicators.items():
        existing_answer = db.query(Answer).filter_by(
            company_id=company_id,
            year=year,
            indicator_id=indicator_id
        ).first()

        if existing_answer:
            # Update existing with real data
            existing_answer.answer_value = data['value']
            existing_answer.source = data['source']
            existing_answer.confidence = 0.95  # High confidence for real data
            existing_answer.notes = f"Real data extracted from company documents - {data['data_type']}"
            updated_count += 1
        else:
            # Create new with real data
            new_answer = Answer(
                session_id=session.id,
                company_id=company_id,
                year=year,
                indicator_id=indicator_id,
                module=get_module_name(indicator_id),
                indicator_name=f"ESG Indicator {indicator_id}",
                answer_value=data['value'],
                source=data['source'],
                confidence=0.95,
                notes=f"Real data extracted from company documents - {data['data_type']}"
            )
            db.add(new_answer)
            updated_count += 1

    db.commit()
    return updated_count

def get_module_name(indicator_id):
    """Get module name from indicator ID"""
    module_map = {
        'M01': 'General & Organizational Profile',
        'M02': 'Sustainability Management & Reporting',
        'M03': 'Governance & Ethics',
        'M05': 'GHG Emissions & Climate Change',
        'M06': 'Energy',
        'M07': 'Water & Effluents',
        'M08': 'Waste & Materials',
        'M14': 'Human Rights',
        'M15': 'Employment Practices',
        'M16': 'Diversity & Inclusion',
        'M17': 'Training & Development',
        'M18': 'Community Relations',
        'M20': 'Data Privacy & Security',
    }

    for module_code, module_name in module_map.items():
        if module_code in indicator_id:
            return module_name

    return "General ESG"

def test_document_extraction(company_id):
    """Test the enhanced document extraction"""

    print("TESTING DOCUMENT-BASED EXTRACTION")
    print("="*50)

    # Run enhanced extraction
    extracted_count = enhance_document_scraping(company_id, 2024)

    if extracted_count > 0:
        print(f"\nSUCCESS: Extracted {extracted_count} real ESG data points!")
        print("All data comes from actual company documents")
        print("NO artificial/intelligent defaults used")

        # Test the results
        from backend.api.routers.indicators import get_indicator_summary
        db = get_session()
        try:
            summary = get_indicator_summary(company_id, 2024, db)
            overall = summary['overall_summary']

            print(f"\nRESULTS:")
            print(f"   * Coverage: {overall['completion_rate']:.1f}%")
            print(f"   * Indicators: {overall['indicators_with_values']}/151")
            print("   * Source: REAL scraped documents only")

        finally:
            db.close()
    else:
        print("No ESG data extracted. Need to upload more company documents.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--company_id", type=int, required=True, help="Company ID to enhance")

    args = parser.parse_args()

    test_document_extraction(args.company_id)