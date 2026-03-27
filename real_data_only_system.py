#!/usr/bin/env python3
"""
REAL DATA ONLY ESG SYSTEM - NO SYNTHETIC DATA
Only uses: Manual Data > Scraped Document Data > Historical Data > Empty
Never generates artificial/synthetic values
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, QuestionnaireSession
import pandas as pd
from datetime import datetime

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

def extract_document_esg_data(company_id: int, year: int, db_session) -> dict:
    """
    Extract ESG indicator values from uploaded/scraped documents.

    Returns only REAL data extracted from sustainability reports,
    annual reports, CSR reports, etc. - NO synthetic generation.
    """
    scraped_entries = db_session.query(ScrapedData).filter_by(
        company_id=company_id,
        year=year
    ).all()

    document_data = {}

    for entry in scraped_entries:
        # Look for ESG indicator mappings in scraped data
        if entry.data_key.startswith('IMP-M'):
            # Direct ESG indicator mapping from real documents
            confidence_level = 0.85  # Default confidence

            # Higher confidence for real PDF extraction
            if entry.source == 'real_pdf_extraction':
                confidence_level = 0.90  # Higher confidence for real document extraction
                print(f"REAL PDF: {entry.data_key} = {entry.data_value}")

            document_data[entry.data_key] = {
                'value': entry.data_value,
                'source': 'scraped',
                'confidence': confidence_level,
                'source_detail': entry.source
            }
        elif 'sustainability' in entry.source.lower() or 'esg' in entry.source.lower() or 'real_pdf' in entry.source.lower():
            # Data from sustainability documents or real PDFs - might need mapping
            confidence_level = 0.8
            if 'real_pdf' in entry.source.lower():
                confidence_level = 0.85  # Higher confidence for real PDFs

            document_data[f"extracted_{entry.data_key}"] = {
                'value': entry.data_value,
                'source': 'scraped',
                'confidence': confidence_level,
                'source_detail': entry.source
            }

    print(f"Found {len(document_data)} ESG values from uploaded documents")
    return document_data

def get_historical_data(company_id: int, year: int, db_session) -> dict:
    """
    Get historical ESG data from previous years for this company.
    Only returns actual historical values, no generation.
    """
    historical_data = {}

    # Look for previous year data (year-1, year-2, etc.)
    for lookback_year in [year-1, year-2, year-3]:
        if lookback_year < 2020:  # Don't go too far back
            break

        previous_answers = db_session.query(Answer).filter_by(
            company_id=company_id,
            year=lookback_year
        ).filter(Answer.answer_value.isnot(None)).filter(Answer.answer_value != '').all()

        for answer in previous_answers:
            if answer.indicator_id not in historical_data:
                # Only use if it's real data (manual or scraped, not calculated)
                if answer.source in ['manual', 'scraped'] and answer.confidence >= 0.7:
                    historical_data[answer.indicator_id] = {
                        'value': answer.answer_value,
                        'source': 'historical',
                        'confidence': 0.5,  # Lower confidence for historical data
                        'source_detail': f"FY{lookback_year} {answer.source} data",
                        'original_year': lookback_year
                    }

    print(f"Found {len(historical_data)} indicators from historical data")
    return historical_data

def process_real_data_only(company_id, year=2024, db_session=None):
    """
    Process ESG indicators using ONLY real data sources.
    No synthetic/artificial data generation.

    Priority:
    1. Manual data (user input) - HIGHEST
    2. Scraped document data (PDFs, reports) - HIGH
    3. Historical data (previous years) - MEDIUM
    4. Missing/Empty - if no real data exists
    """

    db = db_session or get_session()
    should_close_db = db_session is None

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print(f"REAL DATA ONLY ESG SYSTEM")
        print("=" * 80)
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("SOURCES: Manual Data > Fresh Scraped Data > Document Data > Historical Data (if no fresh data) > Empty")
        print("PRIORITY: FRESH REAL DATA OVER HISTORICAL DATA")
        print("NO SYNTHETIC DATA GENERATION")
        print("=" * 80)

        # Step 1: Load target indicators
        all_indicators = load_all_151_indicators()
        print(f"Target indicators: {len(all_indicators)}")

        # Step 2: Get existing manual data
        existing_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        manual_data = {}
        for answer in existing_answers:
            manual_data[answer.indicator_id] = {
                'value': answer.answer_value,
                'source': answer.source,
                'confidence': answer.confidence,
                'answer_id': answer.id
            }

        print(f"Existing manual/input data: {len(manual_data)}")

        # Step 3: Extract document data
        document_data = extract_document_esg_data(company_id, year, db)

        # Step 4: Get historical data
        historical_data = get_historical_data(company_id, year, db)

        # Step 5: Get or create session
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

        # Step 6: Process each indicator with real data only
        stats = {
            'preserved_manual': 0,
            'added_document': 0,
            'added_historical': 0,
            'missing_data': 0
        }

        for indicator in all_indicators:
            indicator_id = indicator['id']

            # Priority 1: Preserve existing manual data
            if indicator_id in manual_data:
                existing = manual_data[indicator_id]
                if existing['source'] in ['manual', 'scraped'] and existing['confidence'] >= 0.7:
                    stats['preserved_manual'] += 1
                    print(f"KEEP {indicator_id}: {existing['source']} (confidence: {existing['confidence']:.1f})")
                    continue

            # Priority 2: Use FRESH scraped data (preferred over historical)
            fresh_sources = ['web_scraped_real', 'financial_official', 'company_website', 'regulatory_filing', 'esg_documents']
            fresh_data = None

            # Check for fresh scraped data first
            for source in fresh_sources:
                fresh_scraped = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    source=source,
                    data_key=indicator_id
                ).first()

                if fresh_scraped and fresh_scraped.data_value:
                    fresh_data = {
                        'value': fresh_scraped.data_value,
                        'source': f'fresh_{source}',
                        'confidence': 0.9  # High confidence for fresh data
                    }
                    break

            if fresh_data:
                # Update or create with FRESH data
                existing_answer = db.query(Answer).filter_by(
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year
                ).first()

                if existing_answer:
                    existing_answer.answer_value = fresh_data['value']
                    existing_answer.source = fresh_data['source']
                    existing_answer.confidence = fresh_data['confidence']
                else:
                    new_answer = Answer(
                        session_id=session.id,
                        company_id=company_id,
                        indicator_id=indicator_id,
                        year=year,
                        answer_value=fresh_data['value'],
                        source=fresh_data['source'],
                        confidence=fresh_data['confidence']
                    )
                    db.add(new_answer)

                stats['added_document'] += 1
                print(f"FRESH {indicator_id}: Fresh {fresh_data['source']} data (confidence: {fresh_data['confidence']:.1f})")
                continue

            # Priority 3: Use document-extracted data (if no fresh data)
            if indicator_id in document_data:
                doc_data = document_data[indicator_id]

                # Update or create with document data
                existing_answer = db.query(Answer).filter_by(
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year
                ).first()

                if existing_answer:
                    existing_answer.answer_value = doc_data['value']
                    existing_answer.source = doc_data['source']
                    existing_answer.confidence = doc_data['confidence']
                else:
                    new_answer = Answer(
                        session_id=session.id,
                        company_id=company_id,
                        indicator_id=indicator_id,
                        year=year,
                        answer_value=doc_data['value'],
                        source=doc_data['source'],
                        confidence=doc_data['confidence']
                    )
                    db.add(new_answer)

                stats['added_document'] += 1
                print(f"DOC {indicator_id}: Document data added (confidence: {doc_data['confidence']:.1f})")
                continue

            # Priority 4: Use historical data ONLY if no fresh scraped data exists
            if indicator_id in historical_data:
                hist_data = historical_data[indicator_id]

                # Check if we already have fresh scraped data for this indicator
                has_fresh_data = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    data_key=indicator_id
                ).filter(ScrapedData.source.in_(['web_scraped_real', 'financial_official', 'company_website', 'regulatory_filing', 'esg_documents'])).first()

                # Only use historical data if NO fresh data is available
                if not has_fresh_data:

                    existing_answer = db.query(Answer).filter_by(
                        company_id=company_id,
                        indicator_id=indicator_id,
                        year=year
                    ).first()

                    if existing_answer:
                        # Only update if current data is poor quality or missing
                        if not existing_answer.answer_value or existing_answer.confidence < 0.4:
                            existing_answer.answer_value = hist_data['value']
                            existing_answer.source = hist_data['source']
                            existing_answer.confidence = hist_data['confidence']
                            stats['added_historical'] += 1
                            print(f"HIST {indicator_id}: Historical FY{hist_data['original_year']} data")
                    else:
                        new_answer = Answer(
                            session_id=session.id,
                            company_id=company_id,
                            indicator_id=indicator_id,
                            year=year,
                            answer_value=hist_data['value'],
                            source=hist_data['source'],
                            confidence=hist_data['confidence']
                        )
                        db.add(new_answer)
                        stats['added_historical'] += 1
                        print(f"HIST {indicator_id}: Historical FY{hist_data['original_year']} data")
                    continue
                else:
                    # Fresh data exists - skip historical data
                    print(f"SKIP {indicator_id}: Fresh data available - skipping historical")
                    continue

            # Priority 5: Mark as missing data
            stats['missing_data'] += 1
            print(f"MISSING {indicator_id}: No real data available")

        db.commit()

        # Final summary
        total_filled = stats['preserved_manual'] + stats['added_document'] + stats['added_historical']
        coverage = (total_filled / 151) * 100

        print("\n" + "=" * 80)
        print("REAL DATA ONLY - SUMMARY")
        print("=" * 80)
        print(f"SUCCESS: Manual data preserved: {stats['preserved_manual']}")
        print(f"SUCCESS: Document data added: {stats['added_document']}")
        print(f"SUCCESS: Historical data used: {stats['added_historical']}")
        print(f"MISSING: Missing (no real data): {stats['missing_data']}")
        print(f"TOTAL COVERAGE: {total_filled}/151 ({coverage:.1f}%)")
        print(f"NO SYNTHETIC DATA GENERATED")

        if stats['missing_data'] > 0:
            print(f"\nTo improve coverage:")
            print(f"   1. Upload sustainability reports/ESG documents")
            print(f"   2. Add manual data entry for key indicators")
            print(f"   3. Import data from previous years")

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

def clear_synthetic_data(company_id, year=2024, db_session=None):
    """
    Remove any existing synthetic/calculated data, keeping only real data.
    """
    db = db_session or get_session()
    should_close_db = db_session is None

    try:
        # Find and remove synthetic data
        synthetic_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).filter(Answer.source.in_(['calculated', 'generated'])).all()

        removed_count = len(synthetic_answers)
        for answer in synthetic_answers:
            db.delete(answer)

        db.commit()
        print(f"Removed {removed_count} synthetic data entries")
        return removed_count

    finally:
        if should_close_db:
            db.close()

def main():
    parser = argparse.ArgumentParser(description="Real Data Only ESG System - No Synthetic Generation")
    parser.add_argument("--company_id", type=int, required=True, help="Company ID")
    parser.add_argument("--year", type=int, default=2024, help="Year")
    parser.add_argument("--clear_synthetic", action="store_true", help="Remove existing synthetic data first")

    args = parser.parse_args()

    if args.clear_synthetic:
        print("Clearing existing synthetic data...")
        clear_synthetic_data(args.company_id, args.year)
        print()

    result = process_real_data_only(args.company_id, args.year)

    print(f"\nFINAL RESULT: {result}/151 indicators with REAL DATA ONLY")
    print("Zero synthetic data generated - only authentic ESG data used")

if __name__ == "__main__":
    main()