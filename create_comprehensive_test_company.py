#!/usr/bin/env python3
"""
Create a comprehensive test company with all 151 ESG indicators populated.
This fixes the session_id constraint error by creating QuestionnaireSession first.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, QuestionnaireSession, Answer
from sqlalchemy import text
from datetime import datetime
import csv

def load_indicators_from_csv():
    """Load all 151 indicators from the CSV questionnaire file"""
    indicators = []
    csv_path = "Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv"

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:  # Handle BOM
            lines = file.readlines()

        # Find the header row that contains "Impactree ID"
        header_line_idx = -1
        for i, line in enumerate(lines):
            if "Impactree ID" in line and "Module" in line and "Indicator" in line:
                header_line_idx = i
                break

        if header_line_idx == -1:
            raise ValueError("Could not find header row in CSV")

        # Parse the header and data rows
        header_line = lines[header_line_idx].strip()
        headers = [h.strip().replace('"', '') for h in header_line.split(',')]

        print(f"Found CSV headers: {headers[:6]}...")  # Show first few headers

        # Parse data rows starting after header
        for line in lines[header_line_idx + 1:]:
            if not line.strip():
                continue

            # Skip section headers (lines that don't start with IMP-)
            if not line.strip().startswith('IMP-M'):
                continue

            # Parse the CSV row manually to handle embedded commas
            row_parts = []
            current_field = ""
            in_quotes = False

            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    row_parts.append(current_field.strip())
                    current_field = ""
                else:
                    current_field += char

            # Add the last field
            if current_field:
                row_parts.append(current_field.strip())

            # Create row dict
            if len(row_parts) >= 4 and row_parts[0].startswith('IMP-M'):
                indicators.append({
                    'id': row_parts[0].strip(),
                    'module': row_parts[1].strip() if len(row_parts) > 1 else '',
                    'name': row_parts[2].strip() if len(row_parts) > 2 else '',
                    'question': row_parts[3].strip() if len(row_parts) > 3 else '',
                    'format': row_parts[4].strip() if len(row_parts) > 4 else ''
                })

    except Exception as e:
        print(f"Warning: Could not load from CSV: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: create a basic set of indicators
        return create_fallback_indicators()

    print(f"Loaded {len(indicators)} indicators from CSV: {csv_path}")
    return indicators

def create_fallback_indicators():
    """Fallback indicator set if CSV loading fails"""
    indicators = []
    modules = [
        "General & Organizational Profile",
        "Sustainability Management & Reporting",
        "Governance & Ethics",
        "GHG Emissions & Climate Change",
        "Energy Management",
        "Water Management",
        "Waste Management",
        "Materials & Circular Economy",
        "Biodiversity & Nature",
        "Air Quality & Pollution",
        "Product Stewardship",
        "Supply Chain Management",
        "Occupational Health & Safety",
        "Human Rights",
        "Employment Practices",
        "Training & Development",
        "Diversity & Inclusion",
        "Community Relations",
        "Customer Relations",
        "Data Privacy & Security",
        "Innovation & Technology"
    ]

    # Generate 151 indicators across 21 modules (averaging ~7 per module)
    indicator_count = 1
    for i, module in enumerate(modules, 1):
        indicators_in_module = 7 if i <= 11 else 8  # 77 + 74 = 151
        for j in range(1, indicators_in_module + 1):
            indicators.append({
                'id': f'IMP-M{i:02d}-I{j:02d}',
                'module': module,
                'name': f'{module} Indicator {j}',
                'question': f'Sample question for {module} indicator {j}',
                'format': 'Text'
            })
            indicator_count += 1
            if indicator_count > 151:
                break
        if indicator_count > 151:
            break

    return indicators[:151]  # Ensure exactly 151

def create_comprehensive_test_company():
    """Create test company with all 151 indicators populated"""
    db = get_session()

    try:
        # 1. Check if comprehensive test company already exists
        test_company = db.query(Company).filter(
            Company.name.like("%COMPREHENSIVE ESG TEST%")
        ).first()

        if test_company:
            print(f"Found existing test company: {test_company.name} (ID: {test_company.id})")
            company_id = test_company.id
        else:
            # Create new comprehensive test company
            test_company = Company(
                name="COMPREHENSIVE ESG TEST COMPANY",
                ticker="CTEST",
                lei="TEST123456789012345678",
                company_number="TEST999999",
                jurisdiction="IN",
                sector="Technology",
                region="APAC",
                status="Active",
                incorporation_date="2020-01-01",
                created_at=datetime.utcnow()
            )
            db.add(test_company)
            db.flush()
            company_id = test_company.id
            print(f"Created test company: {test_company.name} (ID: {company_id})")

        # 2. Create questionnaire session for 2024
        year = 2024
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
            print(f"Created questionnaire session (ID: {session.id}) for year {year}")
        else:
            print(f"Using existing session (ID: {session.id}) for year {year}")

        # 3. Clear existing answers for this session (if any)
        db.execute(text("DELETE FROM answers WHERE session_id = :session_id"),
                  {"session_id": session.id})
        print("Cleared existing answers for session")

        # 4. Load all 151 indicators from CSV file
        indicators = load_indicators_from_csv()
        print(f"Will create {len(indicators)} indicator answers")

        # 5. Create comprehensive test answers for all indicators
        indicators_created = 0
        for indicator_data in indicators:
            indicator_id = indicator_data['id']
            module_name = indicator_data['module']
            indicator_name = indicator_data['name']

            # Create sample answer based on indicator type
            answer_value = generate_sample_answer(indicator_data)

            answer = Answer(
                session_id=session.id,
                company_id=company_id,
                year=year,
                indicator_id=indicator_id,
                module=module_name,
                indicator_name=indicator_name,
                answer_value=answer_value,
                source="manual",  # Use "manual" so CompanyYearProcessor preserves this data
                confidence=0.95,
                notes=f"Comprehensive test data for {indicator_name}"
            )
            db.add(answer)
            indicators_created += 1

        # 6. Update session with completed status
        session.answered_questions = indicators_created
        session.status = "completed"

        db.commit()
        print(f"\nSUCCESS: Created comprehensive test company with {indicators_created}/151 indicators!")
        print(f"   Company: {test_company.name} (ID: {company_id})")
        print(f"   Session: {session.id}")
        print(f"   Year: {year}")
        print(f"   Total Indicators: {indicators_created}")

        return company_id, session.id

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        db.close()

def generate_sample_answer(indicator_data):
    """Generate realistic sample answer based on indicator metadata"""
    indicator_name = indicator_data['name'].lower()
    question = indicator_data.get('question', '').lower()
    format_type = indicator_data.get('format', '').lower()

    # Yes/No responses
    if 'yes / no' in format_type or any(term in question for term in ['has your', 'does your', 'do you have']):
        return "Yes"

    # Numeric indicators
    if any(term in indicator_name for term in ['energy', 'water', 'emissions', 'waste', 'percentage', 'kwh', 'mwh', 'tonnes', 'cubic']):
        if 'percentage' in indicator_name or '%' in format_type:
            return "87.5%"
        elif 'energy' in indicator_name or 'kwh' in format_type:
            return "45,600 MWh"
        elif 'water' in indicator_name or 'cubic' in format_type:
            return "125,400 cubic meters"
        elif 'emissions' in indicator_name or 'tco2' in format_type:
            return "12,850 tCO2e"
        elif 'waste' in indicator_name:
            return "2,450 tonnes"
        else:
            return "1,250"

    # Dates
    elif 'date' in format_type or 'date' in indicator_name:
        return "2023-12-31"

    # Numbers
    elif 'number' in format_type:
        return "42"

    # Policy/compliance indicators
    elif any(term in indicator_name for term in ['policy', 'procedure', 'assessment', 'audit', 'certification', 'compliance']):
        return "Yes - Comprehensive policy implemented with regular monitoring and annual review process."

    # Text/Description indicators
    else:
        return f"Comprehensive {indicator_name} measures implemented across all operations with regular monitoring, stakeholder engagement, and annual reporting. Best-in-class practices adopted with continuous improvement focus."

if __name__ == "__main__":
    print("Creating Comprehensive ESG Test Company...")
    company_id, session_id = create_comprehensive_test_company()

    if company_id:
        print(f"\nNext Step: Test the ESG processing with company ID {company_id}")
        print("   You can now run the pipeline for this company to see all 151 indicators!")
        print(f"   Command: python test_processing.py --company_id={company_id} --year=2024")
    else:
        print("Failed to create test company. Please check the error messages above.")