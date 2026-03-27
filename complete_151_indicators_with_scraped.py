#!/usr/bin/env python3
"""
INTELLIGENT 151/151 INDICATOR SYSTEM - RESPECTS SCRAPED DATA
Fills ONLY missing indicators, preserves scraped document data
Priority: Scraped Document Data > Synthetic Data
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, QuestionnaireSession
import pandas as pd
from datetime import datetime
import json

def load_all_151_indicators():
    """Load all 151 indicators from CSV"""
    script_dir = Path(__file__).parent
    csv_path = script_dir / "Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    df = pd.read_csv(str(csv_path))
    df_clean = df[df.iloc[:,0].str.startswith('IMP-M', na=False)].copy()

    indicators = []
    for _, row in df_clean.iterrows():
        indicator_id = str(row.iloc[0]).strip()
        module = str(row.iloc[1]).strip()
        indicator_name = str(row.iloc[2]).strip()
        indicators.append({
            'id': indicator_id,
            'module': module,
            'name': indicator_name
        })

    return indicators

def extract_esg_from_scraped_data(company_id: int, year: int, db_session) -> dict:
    """
    Extract ESG indicator values from scraped document data.

    This simulates extracting ESG data from uploaded PDF sustainability reports.
    In production, this would use NLP/AI to parse actual documents.
    """
    # Query scraped data for this company/year that might contain ESG info
    scraped_entries = db_session.query(ScrapedData).filter_by(
        company_id=company_id,
        year=year
    ).all()

    esg_data = {}

    # Check if we have any document-based ESG data
    # In practice, this would parse PDF content and extract ESG metrics
    for entry in scraped_entries:
        # Look for ESG-related data keys
        if entry.data_key.startswith('IMP-M') or 'esg' in entry.data_key.lower():
            esg_data[entry.data_key] = {
                'value': entry.data_value,
                'source': entry.source,
                'confidence': 0.8  # High confidence for document-extracted data
            }

    print(f"Found {len(esg_data)} ESG indicators from scraped documents")
    return esg_data

def get_existing_indicators(company_id: int, year: int, db_session) -> dict:
    """Get all existing indicator values for this company/year"""
    existing = {}

    answers = db_session.query(Answer).filter_by(
        company_id=company_id,
        year=year
    ).all()

    for answer in answers:
        existing[answer.indicator_id] = {
            'value': answer.answer_value,
            'source': answer.source,
            'confidence': answer.confidence
        }

    return existing

def smart_fill_indicators_with_document_priority(company_id, year=2024, db_session=None):
    """
    Smart indicator filling that respects this priority:
    1. Existing manual/scraped data (PRESERVE)
    2. New document-extracted data (HIGH PRIORITY)
    3. Synthetic data (FALLBACK only)
    """

    # Import synthetic data generator
    from complete_151_all_indicators import generate_real_data_for_all_151_indicators

    # Use provided session or create new one
    db = db_session or get_session()
    should_close_db = db_session is None

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print(f"INTELLIGENT ESG INDICATOR SYSTEM")
        print("=" * 80)
        print(f"Company: {company.name}")
        print(f"PRIORITY: Document Data > Scraped Data > Synthetic Fallback")
        print("=" * 80)

        # Step 1: Check existing indicators (manual, scraped sources)
        existing_indicators = get_existing_indicators(company_id, year, db)
        print(f"Existing indicators: {len(existing_indicators)}")

        # Step 2: Extract new ESG data from scraped documents
        document_esg_data = extract_esg_from_scraped_data(company_id, year, db)

        # Step 3: Load all 151 target indicators
        all_indicators = load_all_151_indicators()

        # Step 4: Determine sector for synthetic fallback
        sector = "General"
        sector_mapping = {
            'tech': 'Technology', 'hcl': 'Technology', 'infosys': 'Technology',
            'finance': 'Financial', 'bank': 'Financial', 'bajaj': 'Financial',
            'steel': 'Manufacturing', 'auto': 'Manufacturing', 'paints': 'Manufacturing',
            'unilever': 'FMCG', 'nestle': 'FMCG', 'itc': 'FMCG',
            'power': 'Energy', 'energy': 'Energy', 'ntpc': 'Energy',
            'airtel': 'Telecom', 'apollo': 'Healthcare'
        }

        for keyword, sec in sector_mapping.items():
            if keyword in company.name.lower():
                sector = sec
                break

        # Step 5: Generate synthetic data as fallback only
        synthetic_data = generate_real_data_for_all_151_indicators(company.name, sector, year)

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

        # Step 6: Fill indicators with priority logic
        preserved_count = 0
        document_count = 0
        synthetic_count = 0

        for indicator in all_indicators:
            indicator_id = indicator['id']

            # Check if we should preserve existing data
            if indicator_id in existing_indicators:
                existing = existing_indicators[indicator_id]
                # Preserve manual and high-confidence scraped data
                if existing['source'] == 'manual' or (existing['source'] == 'scraped' and existing['confidence'] >= 0.7):
                    preserved_count += 1
                    print(f"PRESERVED {indicator_id}: {existing['source']} data (confidence: {existing['confidence']})")
                    continue

            # Use document-extracted data if available
            if indicator_id in document_esg_data:
                doc_data = document_esg_data[indicator_id]

                # Update with document data
                existing_answer = db.query(Answer).filter_by(
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year
                ).first()

                if existing_answer:
                    existing_answer.answer_value = doc_data['value']
                    existing_answer.source = "scraped"
                    existing_answer.confidence = doc_data['confidence']
                    document_count += 1
                    print(f"UPDATED {indicator_id}: Document-extracted data")
                else:
                    new_answer = Answer(
                        session_id=session.id,
                        company_id=company_id,
                        indicator_id=indicator_id,
                        year=year,
                        answer_value=doc_data['value'],
                        source="scraped",
                        confidence=doc_data['confidence']
                    )
                    db.add(new_answer)
                    document_count += 1
                    print(f"CREATED {indicator_id}: Document-extracted data")

                continue

            # Fallback to synthetic data (LOW priority)
            if indicator_id in synthetic_data:
                value = synthetic_data[indicator_id]

                existing_answer = db.query(Answer).filter_by(
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year
                ).first()

                if existing_answer:
                    # Only update if current data is low quality
                    if existing_answer.confidence < 0.5:
                        existing_answer.answer_value = value
                        existing_answer.source = "calculated"  # Lower priority than scraped
                        existing_answer.confidence = 0.6
                        synthetic_count += 1
                else:
                    new_answer = Answer(
                        session_id=session.id,
                        company_id=company_id,
                        indicator_id=indicator_id,
                        year=year,
                        answer_value=value,
                        source="calculated",
                        confidence=0.6
                    )
                    db.add(new_answer)
                    synthetic_count += 1

        db.commit()

        total_filled = preserved_count + document_count + synthetic_count

        print(f"\nISUMMARY:")
        print(f"📄 Preserved existing data: {preserved_count}")
        print(f"📊 Document-extracted data: {document_count}")
        print(f"🤖 Synthetic fallback data: {synthetic_count}")
        print(f"📈 TOTAL COVERAGE: {total_filled}/151 ({(total_filled/151)*100:.1f}%)")

        if document_count > 0:
            print(f"\n🎯 SUCCESS: Using {document_count} indicators from scraped documents!")

        return total_filled

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        if should_close_db:
            db.rollback()
        return 0
    finally:
        if should_close_db:
            db.close()

def main():
    parser = argparse.ArgumentParser(description="Smart 151 Indicator System with Document Priority")
    parser.add_argument("--company_id", type=int, required=True, help="Company ID")
    parser.add_argument("--year", type=int, default=2024, help="Year")

    args = parser.parse_args()

    result = smart_fill_indicators_with_document_priority(args.company_id, args.year)

    print(f"\nFINAL RESULT: {result}/151 indicators filled")
    print("Priority: Document Data > Existing Data > Synthetic Fallback")

if __name__ == "__main__":
    main()