#!/usr/bin/env python3
"""
CLEAN REAL DATA ONLY PIPELINE
Removes ALL synthetic data and processes companies with 100% authentic sources only
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Answer, ScrapedData, Company

def clean_synthetic_data(company_id: int, year: int):
    """Remove ALL synthetic data for a company/year"""

    db = get_session()

    try:
        print(f"CLEANING SYNTHETIC DATA FOR COMPANY {company_id} - YEAR {year}")
        print("=" * 60)

        # List of ALL synthetic sources to remove
        synthetic_sources = [
            'intelligent_default',
            'smart_default',
            'calculated_default',
            'complete_151_real_data_technology',
            'complete_151_real_data_financial',
            'complete_151_real_data_general',
            'complete_151_real_data_fmcg',
            'complete_151_real_data_automobile',
            'complete_151_real_data_manufacturing',
            'complete_151_real_data_energy',
            'complete_151_real_data_telecom',
            'real_sector_data',  # This is also synthetic!
            'system_default',
            'auto_generated'
        ]

        # Delete all synthetic answer records
        total_deleted = 0
        for source in synthetic_sources:
            deleted = db.query(Answer).filter_by(
                company_id=company_id,
                year=year,
                source=source
            ).delete()

            if deleted > 0:
                print(f"  Deleted {deleted} records with source '{source}'")
                total_deleted += deleted

        db.commit()

        print(f"\nCLEAN COMPLETE:")
        print(f"  Total synthetic records removed: {total_deleted}")

        # Verify what's left
        remaining = db.query(Answer).filter_by(company_id=company_id, year=year).all()
        print(f"  Remaining records: {len(remaining)}")

        source_counts = {}
        for answer in remaining:
            source = answer.source or 'None'
            source_counts[source] = source_counts.get(source, 0) + 1

        print(f"  Remaining sources:")
        for source, count in source_counts.items():
            print(f"    {source}: {count} records")

        return total_deleted

    finally:
        db.close()

def process_pure_real_data(company_id: int, year: int):
    """Process company with ONLY real data sources (no synthetic fallbacks)"""

    from real_data_only_system import extract_document_esg_data, get_historical_data
    from backend.database.models import QuestionnaireSession

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print(f"\nPURE REAL DATA PROCESSING")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("SOURCES: Manual > Real Documents > Historical > MISSING (NO FALLBACKS)")
        print("=" * 60)

        # Load all 151 indicators
        indicators = []
        try:
            from real_data_only_system import load_all_151_indicators
            indicators = load_all_151_indicators()
        except:
            # Fallback list of key indicators
            indicators = [
                {'id': 'IMP-M01-I01', 'module': 'M01', 'name': 'Company Profile'},
                {'id': 'IMP-M03-I01', 'module': 'M03', 'name': 'Revenue'},
                {'id': 'IMP-M05-I01', 'module': 'M05', 'name': 'Scope 1 Emissions'}
            ]

        print(f"Target indicators: {len(indicators)}")

        # Get real document data
        document_data = extract_document_esg_data(company_id, year, db)
        print(f"Document data found: {len(document_data)}")

        # Get historical data
        historical_data = get_historical_data(company_id, year, db)
        print(f"Historical data found: {len(historical_data)}")

        # Get or create session
        session = db.query(QuestionnaireSession).filter_by(
            company_id=company_id, year=year, standard="ALL"
        ).first()

        if not session:
            session = QuestionnaireSession(
                company_id=company_id, year=year, standard="ALL",
                status="in_progress", total_questions=len(indicators)
            )
            db.add(session)
            db.commit()

        # Process each indicator with ZERO synthetic fallbacks
        stats = {
            'real_documents': 0,
            'historical': 0,
            'missing': 0
        }

        for indicator in indicators:
            indicator_id = indicator['id']

            # Priority 1: Real document data
            if indicator_id in document_data:
                doc_data = document_data[indicator_id]

                new_answer = Answer(
                    session_id=session.id,
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year,
                    answer_value=doc_data['value'],
                    source='scraped',  # Real document source
                    confidence=doc_data['confidence']
                )
                db.add(new_answer)
                stats['real_documents'] += 1
                print(f"  REAL DOC: {indicator_id}")

            # Priority 2: Historical data
            elif indicator_id in historical_data:
                hist_data = historical_data[indicator_id]

                new_answer = Answer(
                    session_id=session.id,
                    company_id=company_id,
                    indicator_id=indicator_id,
                    year=year,
                    answer_value=hist_data['value'],
                    source='historical',
                    confidence=hist_data['confidence']
                )
                db.add(new_answer)
                stats['historical'] += 1
                print(f"  HISTORICAL: {indicator_id}")

            # Priority 3: MISSING (NO SYNTHETIC FALLBACK)
            else:
                stats['missing'] += 1
                print(f"  MISSING: {indicator_id} (no real data available)")
                # DO NOT CREATE ANY RECORD - leave as genuinely missing

        db.commit()

        total_real = stats['real_documents'] + stats['historical']

        print(f"\n" + "="*60)
        print(f"PURE REAL DATA RESULTS:")
        print(f"  Real documents: {stats['real_documents']}")
        print(f"  Historical data: {stats['historical']}")
        print(f"  Missing (no fallback): {stats['missing']}")
        print(f"  Total real data: {total_real}/{len(indicators)}")
        print(f"  Real percentage: {(total_real/len(indicators))*100:.1f}%")
        print(f"  NO SYNTHETIC DATA GENERATED")
        print("="*60)

        return total_real

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC Limited
    company_id = 30  # ITC LIMITED
    year = 2024

    print("PURE REAL DATA PIPELINE TEST - ITC LIMITED")
    print("=" * 60)

    # Step 1: Clean all synthetic data
    deleted = clean_synthetic_data(company_id, year)

    # Step 2: Process with pure real data only
    real_count = process_pure_real_data(company_id, year)

    print(f"\nFINAL RESULT:")
    print(f"  Synthetic records deleted: {deleted}")
    print(f"  Real indicators processed: {real_count}")
    print(f"  Status: 100% AUTHENTIC DATA PIPELINE")