#!/usr/bin/env python3
"""
Comprehensive 151 ESG Indicator Mapping System
Maps scraped document data to ALL 151 indicators across 21 modules
Goal: 151/151 indicators with real scraped document data
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, QuestionnaireSession
import pandas as pd
import re

def create_comprehensive_indicator_mapping():
    """Create comprehensive mapping from scraped data keys to all 151 ESG indicators"""

    # Load all indicators from CSV
    df = pd.read_csv("Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv")
    df_clean = df[df.iloc[:,0].str.startswith('IMP-M', na=False)].copy()

    # Enhanced mapping - covers all 21 modules
    comprehensive_mapping = {
        # M01 - GENERAL & ORGANIZATIONAL PROFILE
        'Company Name': 'IMP-M01-I01',
        'Legal Name': 'IMP-M01-I01',
        'CIN': 'IMP-M01-I01',
        'Incorporation Date': 'IMP-M01-I01',
        'Registered Address': 'IMP-M01-I01',
        'Website': 'IMP-M01-I01',
        'Business Activities': 'IMP-M01-I02',
        'Main Products': 'IMP-M01-I02',
        'Revenue Segments': 'IMP-M01-I02',
        'Geographic Presence': 'IMP-M01-I03',
        'Number of Facilities': 'IMP-M01-I03',
        'Manufacturing Locations': 'IMP-M01-I03',
        'Office Locations': 'IMP-M01-I03',
        'Reporting Boundary': 'IMP-M01-I04',
        'Financial Year': 'IMP-M01-I04',
        'Subsidiaries': 'IMP-M01-I05',
        'Joint Ventures': 'IMP-M01-I05',
        'Associate Companies': 'IMP-M01-I05',
        'Stakeholder Groups': 'IMP-M01-I06',
        'Stakeholder Engagement': 'IMP-M01-I06',
        'Value Chain Mapping': 'IMP-M01-I07',

        # M02 - SUSTAINABILITY MANAGEMENT & REPORTING
        'Sustainability Policy': 'IMP-M02-I01',
        'ESG Policy': 'IMP-M02-I01',
        'Environment Policy': 'IMP-M02-I01',
        'Board Approved Policy': 'IMP-M02-I01',
        'Sustainability Goals': 'IMP-M02-I02',
        'ESG Targets': 'IMP-M02-I02',
        'Performance Metrics': 'IMP-M02-I02',
        'ISO Certification': 'IMP-M02-I03',
        'ISO 14001': 'IMP-M02-I03',
        'ISO 50001': 'IMP-M02-I03',
        'OHSAS 18001': 'IMP-M02-I03',
        'SA 8000': 'IMP-M02-I03',
        'UN Global Compact': 'IMP-M02-I04',
        'Science Based Targets': 'IMP-M02-I04',
        'External Assurance': 'IMP-M02-I05',
        'Third Party Verification': 'IMP-M02-I05',
        'Independent Audit': 'IMP-M02-I05',
        'Assurance Provider': 'IMP-M02-I05',

        # M03 - FINANCIAL PERFORMANCE
        'Total Revenue': 'IMP-M03-I01',
        'Net Sales': 'IMP-M03-I01',
        'Turnover': 'IMP-M03-I01',
        'Revenue': 'IMP-M03-I01',
        'Profit Before Tax': 'IMP-M03-I02',
        'PBT': 'IMP-M03-I02',
        'Net Profit': 'IMP-M03-I03',
        'Net Income': 'IMP-M03-I03',
        'PAT': 'IMP-M03-I03',
        'EBITDA': 'IMP-M03-I04',
        'Operating Profit': 'IMP-M03-I04',
        'Market Capitalization': 'IMP-M03-I05',
        'Market Cap': 'IMP-M03-I05',
        'Tax expense': 'IMP-M03-I06',
        'Income Tax': 'IMP-M03-I06',
        'Tax Paid': 'IMP-M03-I06',
        'Current Tax': 'IMP-M03-I06',
        'Deferred Tax': 'IMP-M03-I06',
        'Total Assets': 'IMP-M03-I07',
        'Balance Sheet Total': 'IMP-M03-I07',
        'Dividend Payment': 'IMP-M03-I08',
        'Dividend per Share': 'IMP-M03-I08',
        'Economic Value': 'IMP-M03-I09',

        # M04 - RESEARCH & DEVELOPMENT
        'R&D Expenditure': 'IMP-M04-I01',
        'Research Investment': 'IMP-M04-I01',
        'Development Costs': 'IMP-M04-I01',
        'Innovation Spend': 'IMP-M04-I01',
        'R&D Facilities': 'IMP-M04-I02',
        'Research Centers': 'IMP-M04-I02',
        'Innovation Labs': 'IMP-M04-I02',
        'Patent Applications': 'IMP-M04-I03',
        'Patents Filed': 'IMP-M04-I03',
        'Intellectual Property': 'IMP-M04-I03',
        'Innovation Projects': 'IMP-M04-I04',
        'New Product Development': 'IMP-M04-I04',
        'Technology Partnerships': 'IMP-M04-I05',
        'University Collaboration': 'IMP-M04-I05',
        'Open Innovation': 'IMP-M04-I06',

        # M05 - CLIMATE CHANGE & GHG EMISSIONS
        'Scope 1 Emissions': 'IMP-M05-I01',
        'Direct Emissions': 'IMP-M05-I01',
        'GHG Scope 1': 'IMP-M05-I01',
        'Scope 2 Emissions': 'IMP-M05-I02',
        'Indirect Emissions': 'IMP-M05-I02',
        'Electricity Emissions': 'IMP-M05-I02',
        'scope_3_emissions_total': 'IMP-M05-I03',
        'Scope 3 Emissions': 'IMP-M05-I03',
        'Value Chain Emissions': 'IMP-M05-I03',
        'Total GHG Emissions': 'IMP-M05-I04',
        'Carbon Footprint': 'IMP-M05-I04',
        'carbon_intensity_per_revenue': 'IMP-M05-I05',
        'Carbon Intensity': 'IMP-M05-I05',
        'Emissions per Revenue': 'IMP-M05-I05',
        'Climate Risk Assessment': 'IMP-M05-I06',
        'Climate Adaptation': 'IMP-M05-I07',
        'Carbon Offset': 'IMP-M05-I08',

        # M06 - ENERGY
        'Total Energy Consumption': 'IMP-M06-I01',
        'Energy Use': 'IMP-M06-I01',
        'Energy Consumed': 'IMP-M06-I01',
        'renewable_energy_target': 'IMP-M06-I02',
        'Renewable Energy': 'IMP-M06-I02',
        'Green Energy': 'IMP-M06-I02',
        'Solar Energy': 'IMP-M06-I02',
        'Wind Energy': 'IMP-M06-I02',
        'energy_intensity_per_revenue': 'IMP-M06-I03',
        'Energy Intensity': 'IMP-M06-I03',
        'Energy Efficiency': 'IMP-M06-I04',
        'Energy Savings': 'IMP-M06-I04',
        'Energy Conservation': 'IMP-M06-I04',
        'Grid Electricity': 'IMP-M06-I05',
        'Purchased Electricity': 'IMP-M06-I05',
        'Energy Source': 'IMP-M06-I06',
        'Fuel Consumption': 'IMP-M06-I07',

        # M07 - WATER & EFFLUENTS
        'Water Consumption': 'IMP-M07-I01',
        'Water Intake': 'IMP-M07-I01',
        'Fresh Water': 'IMP-M07-I01',
        'Water Withdrawal': 'IMP-M07-I02',
        'Groundwater': 'IMP-M07-I02',
        'Surface Water': 'IMP-M07-I02',
        'water_recycling_rate': 'IMP-M07-I03',
        'Water Recycling': 'IMP-M07-I03',
        'Recycled Water': 'IMP-M07-I03',
        'Water Reuse': 'IMP-M07-I03',
        'Water Discharge': 'IMP-M07-I04',
        'Wastewater': 'IMP-M07-I04',
        'Effluent': 'IMP-M07-I04',
        'water_quality_parameters': 'IMP-M07-I05',
        'Water Quality': 'IMP-M07-I05',
        'BOD': 'IMP-M07-I05',
        'COD': 'IMP-M07-I05',
        'Water Stress': 'IMP-M07-I06',
        'Water Scarcity': 'IMP-M07-I06',
        'Water Conservation': 'IMP-M07-I07',
        'Rainwater Harvesting': 'IMP-M07-I08',
        'Water Treatment': 'IMP-M07-I09',
        'Zero Liquid Discharge': 'IMP-M07-I10',

        # M08 - BIODIVERSITY
        'Biodiversity Policy': 'IMP-M08-I01',
        'Protected Areas': 'IMP-M08-I02',
        'Habitat Conservation': 'IMP-M08-I02',
        'Endangered Species': 'IMP-M08-I03',
        'Species Protection': 'IMP-M08-I03',
        'Ecosystem Impact': 'IMP-M08-I04',
        'Land Use': 'IMP-M08-I05',
        'Deforestation': 'IMP-M08-I06',
        'Forest Conservation': 'IMP-M08-I06',
        'Afforestation': 'IMP-M08-I07',
        'Tree Plantation': 'IMP-M08-I07',
        'IUCN Red List': 'IMP-M08-I08',
        'Biodiversity Monitoring': 'IMP-M08-I09',

        # M09 - WASTE
        'waste_generation_total': 'IMP-M09-I01',
        'Total Waste': 'IMP-M09-I01',
        'Waste Generated': 'IMP-M09-I01',
        'Hazardous Waste': 'IMP-M09-I02',
        'Non-Hazardous Waste': 'IMP-M09-I03',
        'waste_recycling_rate': 'IMP-M09-I04',
        'Waste Recycling': 'IMP-M09-I04',
        'Recycled Waste': 'IMP-M09-I04',
        'Waste to Landfill': 'IMP-M09-I05',
        'Landfill Waste': 'IMP-M09-I05',
        'Waste Disposal': 'IMP-M09-I06',
        'Waste Management': 'IMP-M09-I07',

        # M10 - MATERIALS
        'Raw Materials': 'IMP-M10-I01',
        'Material Consumption': 'IMP-M10-I01',
        'Renewable Materials': 'IMP-M10-I02',
        'Recycled Materials': 'IMP-M10-I03',
        'Material Intensity': 'IMP-M10-I04',
        'Sustainable Materials': 'IMP-M10-I05',
        'Material Efficiency': 'IMP-M10-I06',

        # M11 - POLLUTION & EMISSIONS
        'Air Pollution': 'IMP-M11-I01',
        'NOx Emissions': 'IMP-M11-I01',
        'SOx Emissions': 'IMP-M11-I01',
        'Particulate Matter': 'IMP-M11-I02',
        'PM2.5': 'IMP-M11-I02',
        'PM10': 'IMP-M11-I02',
        'Ozone Depleting': 'IMP-M11-I03',
        'VOC Emissions': 'IMP-M11-I04',
        'Noise Pollution': 'IMP-M11-I05',

        # M12 - CIRCULAR ECONOMY
        'Circular Design': 'IMP-M12-I01',
        'Product Lifecycle': 'IMP-M12-I02',
        'Material Recovery': 'IMP-M12-I03',
        'Resource Efficiency': 'IMP-M12-I04',
        'Closed Loop': 'IMP-M12-I05',

        # M13 - SUPPLY CHAIN
        'Supplier Assessment': 'IMP-M13-I01',
        'supply_chain_esg_assessment': 'IMP-M13-I01',
        'Supplier Audit': 'IMP-M13-I02',
        'Local Sourcing': 'IMP-M13-I03',
        'Supplier Code of Conduct': 'IMP-M13-I04',
        'Supply Chain Risk': 'IMP-M13-I05',
        'Vendor Assessment': 'IMP-M13-I06',
        'Procurement Policy': 'IMP-M13-I07',

        # M14 - EMPLOYMENT
        'Total Employees': 'IMP-M14-I01',
        'Employee Count': 'IMP-M14-I01',
        'Workforce': 'IMP-M14-I01',
        'Headcount': 'IMP-M14-I01',
        'permanent_employees_male': 'IMP-M14-I02',
        'permanent_employees_female': 'IMP-M14-I02',
        'Employee Demographics': 'IMP-M14-I02',
        'Gender Diversity': 'IMP-M14-I02',
        'SG&A (includes employee costs)': 'IMP-M14-I03',
        'Employee Costs': 'IMP-M14-I03',
        'Salary Expenses': 'IMP-M14-I03',
        'Personnel Expense': 'IMP-M14-I03',
        'Staff Costs': 'IMP-M14-I03',
        'Employee Turnover': 'IMP-M14-I04',
        'Attrition Rate': 'IMP-M14-I04',
        'New Hires': 'IMP-M14-I05',
        'Recruitment': 'IMP-M14-I05',
        'Employee Benefits': 'IMP-M14-I06',
        'Temporary Workers': 'IMP-M14-I07',
        'Contract Workers': 'IMP-M14-I07',
        'Age Diversity': 'IMP-M14-I08',
        'Geographic Diversity': 'IMP-M14-I09',
        'Disability Inclusion': 'IMP-M14-I10',
        'Maternity Leave': 'IMP-M14-I11',
        'Paternity Leave': 'IMP-M14-I11',
        'Parental Leave': 'IMP-M14-I11',
        'Work Life Balance': 'IMP-M14-I12',

        # M15 - LEARNING & DEVELOPMENT
        'Training Hours': 'IMP-M15-I01',
        'employee_training_hours_total': 'IMP-M15-I01',
        'Employee Training': 'IMP-M15-I01',
        'Learning Programs': 'IMP-M15-I01',
        'Skill Development': 'IMP-M15-I02',
        'Leadership Development': 'IMP-M15-I03',
        'Training Investment': 'IMP-M15-I04',
        'Training Programs': 'IMP-M15-I05',
        'E-Learning': 'IMP-M15-I06',
        'Professional Development': 'IMP-M15-I07',
        'Certification Programs': 'IMP-M15-I08',
        'Knowledge Management': 'IMP-M15-I09',
        'Mentoring': 'IMP-M15-I10',

        # M16 - DIVERSITY & EQUAL OPPORTUNITY
        'women_in_leadership_percentage': 'IMP-M16-I01',
        'Female Leadership': 'IMP-M16-I01',
        'Women in Management': 'IMP-M16-I01',
        'Gender Pay Gap': 'IMP-M16-I02',
        'Equal Pay': 'IMP-M16-I02',
        'Board Diversity': 'IMP-M16-I03',
        'Women Directors': 'IMP-M16-I03',
        'Minority Representation': 'IMP-M16-I04',
        'Inclusive Hiring': 'IMP-M16-I05',
        'Diversity Policy': 'IMP-M16-I06',

        # M17 - NON-DISCRIMINATION
        'Anti-Discrimination Policy': 'IMP-M17-I01',
        'Harassment Prevention': 'IMP-M17-I02',
        'Grievance Mechanism': 'IMP-M17-I03',
        'Equal Opportunity': 'IMP-M17-I04',

        # M18 - COMMUNITY DEVELOPMENT
        'CSR Spending': 'IMP-M18-I01',
        'CSR Investment': 'IMP-M18-I01',
        'Community Investment': 'IMP-M18-I01',
        'CSR Budget': 'IMP-M18-I01',
        'Net profit (CSR 2% basis)': 'IMP-M18-I04',
        'CSR Eligibility': 'IMP-M18-I04',
        'CSR Requirement': 'IMP-M18-I04',
        'Education Programs': 'IMP-M18-I02',
        'Community Projects': 'IMP-M18-I03',
        'Local Development': 'IMP-M18-I05',
        'Social Programs': 'IMP-M18-I06',

        # M19 - CUSTOMER HEALTH & SAFETY
        'Product Safety': 'IMP-M19-I01',
        'Product Quality': 'IMP-M19-I01',
        'customer_satisfaction_score': 'IMP-M19-I02',
        'Customer Satisfaction': 'IMP-M19-I02',
        'NPS Score': 'IMP-M19-I02',
        'Product Recalls': 'IMP-M19-I03',
        'Safety Incidents': 'IMP-M19-I03',
        'Consumer Protection': 'IMP-M19-I04',
        'Customer Privacy': 'IMP-M19-I05',
        'Data Protection': 'IMP-M19-I05',
        'Product Labeling': 'IMP-M19-I06',
        'Quality Certifications': 'IMP-M19-I07',
        'Customer Complaints': 'IMP-M19-I08',

        # M20 - ECONOMIC PERFORMANCE (Additional)
        'Revenue Growth': 'IMP-M20-I01',
        'Sales Growth': 'IMP-M20-I01',
        'EBITDA': 'IMP-M20-I02',
        'Operating Cash Flow': 'IMP-M20-I02',
        'Capital Expenditure': 'IMP-M20-I03',
        'CAPEX': 'IMP-M20-I03',
        'PPE Purchases': 'IMP-M20-I03',
        'Return on Assets': 'IMP-M20-I04',
        'ROA': 'IMP-M20-I04',
        'Return on Equity': 'IMP-M20-I05',
        'ROE': 'IMP-M20-I05',
        'Debt Ratio': 'IMP-M20-I06',

        # M21 - OCCUPATIONAL HEALTH & SAFETY
        'workplace_injury_rate': 'IMP-M21-I01',
        'Injury Rate': 'IMP-M21-I01',
        'Accident Rate': 'IMP-M21-I01',
        'Lost Time Injuries': 'IMP-M21-I01',
        'Workplace Fatality': 'IMP-M21-I02',
        'Fatal Accidents': 'IMP-M21-I02',
        'Safety Training': 'IMP-M21-I03',
        'Safety Programs': 'IMP-M21-I03',
        'Health Programs': 'IMP-M21-I04',
    }

    return comprehensive_mapping

def extract_comprehensive_esg_data(company_id, year=2024):
    """Extract comprehensive ESG data using enhanced 151-indicator mapping"""

    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return

        print(f"COMPREHENSIVE ESG DATA EXTRACTION - ALL 151 INDICATORS")
        print("=" * 70)
        print(f"Company: {company.name}")
        print(f"Target: Extract real data for ALL 151 indicators")
        print("=" * 70)

        # Get scraped data
        scraped_records = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"Scraped data records: {len(scraped_records)}")

        # Get comprehensive mapping
        mapping = create_comprehensive_indicator_mapping()

        # Extract ESG data using comprehensive mapping
        extracted_data = {}
        source_mapping = {}

        for record in scraped_records:
            data_key = record.data_key
            data_value = record.data_value
            source = record.source

            # Direct match
            if data_key in mapping:
                indicator_id = mapping[data_key]
                extracted_data[indicator_id] = data_value
                source_mapping[indicator_id] = f"scraped_{source}"
            else:
                # Fuzzy matching for partial key matches
                for key, indicator_id in mapping.items():
                    if key.lower() in data_key.lower() or data_key.lower() in key.lower():
                        if indicator_id not in extracted_data:  # Avoid overwriting
                            extracted_data[indicator_id] = data_value
                            source_mapping[indicator_id] = f"scraped_{source}"
                        break

        print(f"\nEXTRACTED ESG INDICATORS: {len(extracted_data)}/151")
        print("Real ESG data extracted:")

        # Get or create session
        session = db.query(QuestionnaireSession).filter_by(
            company_id=company_id,
            year=year,
            standard="ALL"
        ).first()

        if not session:
            session = QuestionnaireSession(
                company_id=company_id,
                year=year,
                standard="ALL",
                status="in_progress",
                total_questions=151
            )
            db.add(session)
            db.commit()
            print(f"Created new questionnaire session for {company.name}")

        # Update database
        updated_count = 0
        for indicator_id, value in extracted_data.items():
            # Check if answer already exists
            existing_answer = db.query(Answer).filter_by(
                company_id=company_id,
                indicator_id=indicator_id,
                year=year
            ).first()

            if existing_answer:
                # Update with real data only if current source is artificial
                if existing_answer.source == 'intelligent_default' or not existing_answer.answer_value:
                    existing_answer.answer_value = value
                    existing_answer.source = source_mapping[indicator_id]
                    updated_count += 1
                    print(f"   {indicator_id}: {value[:60]}{'...' if len(value) > 60 else ''}")
            else:
                # Create new answer with real data
                new_answer = Answer(
                    session_id=session.id,
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year,
                    answer_value=value,
                    source=source_mapping[indicator_id]
                )
                db.add(new_answer)
                updated_count += 1
                print(f"   {indicator_id}: {value[:60]}{'...' if len(value) > 60 else ''}")

        db.commit()

        print(f"\nSUCCESS: Updated {updated_count} indicators with real scraped data")
        print(f"PROGRESS: {len(extracted_data)}/151 indicators now have real data")
        print(f"Coverage: {(len(extracted_data)/151)*100:.1f}%")

        return len(extracted_data)

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Comprehensive 151 ESG Indicator Mapping")
    parser.add_argument("--company_id", type=int, required=True, help="Company ID to process")
    parser.add_argument("--year", type=int, default=2024, help="Year to process")

    args = parser.parse_args()

    result = extract_comprehensive_esg_data(args.company_id, args.year)

    if result > 0:
        print(f"\nCOMPREHENSIVE EXTRACTION COMPLETE")
        print(f"Real indicators extracted: {result}")
        print("All data from authentic company documents")
    else:
        print("\nNo additional real data extracted")

if __name__ == "__main__":
    main()