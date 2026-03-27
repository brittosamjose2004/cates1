#!/usr/bin/env python3
"""
Document-Only ESG Pipeline for Infosys Limited
Extracts data ONLY from scraped documents, no patterns or templates
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, QuestionnaireSession
from datetime import datetime
import json

def run_document_only_pipeline(company_id: int, year: int):
    """
    Run pipeline using ONLY document-extracted data
    Excludes all pattern-based and template data
    """

    print(f"=== DOCUMENT-ONLY PIPELINE FOR COMPANY {company_id} YEAR {year} ===")

    db = get_session()

    try:
        # Get company info
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Error: Company {company_id} not found")
            return

        print(f"Company: {company.name}")

        # Clear existing data for this year
        print(f"\nStep 1: Clearing existing data for {year}...")
        deleted_answers = db.query(Answer).filter(
            Answer.company_id == company_id,
            Answer.year == year
        ).delete()
        print(f"Deleted {deleted_answers} existing answers")

        # Delete questionnaire session
        deleted_session = db.query(QuestionnaireSession).filter(
            QuestionnaireSession.company_id == company_id,
            QuestionnaireSession.year == year
        ).delete()
        print(f"Deleted {deleted_session} questionnaire sessions")

        db.commit()

        # Get ONLY document-based scraped data
        print(f"\nStep 2: Extracting document-based data...")

        document_sources = ['real_pdf_extraction', 'document_mining_patterns', 'brsr_pdf']

        scraped_data = db.query(ScrapedData).filter(
            ScrapedData.company_id == company_id,
            ScrapedData.source.in_(document_sources)
        ).all()

        print(f"Found {len(scraped_data)} document-based data points")

        # Group by source
        by_source = {}
        for item in scraped_data:
            if item.source not in by_source:
                by_source[item.source] = []
            by_source[item.source].append(item)

        for source, items in by_source.items():
            print(f"  {source}: {len(items)} items")

        # Create new answers ONLY from document sources
        print(f"\nStep 3: Creating answers from document sources...")

        created_count = 0

        # Create questionnaire session
        session = QuestionnaireSession(
            company_id=company_id,
            year=year,
            status='completed',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(session)
        db.flush()

        # Process each document-based scraped item
        for item in scraped_data:
            if item.data_key and item.data_value:
                # Create answer
                answer = Answer(
                    company_id=company_id,
                    year=year,
                    session_id=session.id,
                    indicator_id=item.data_key,
                    answer_value=item.data_value,
                    source=item.source,  # Keep original document source
                    confidence=0.9,  # High confidence for document extraction
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_verified=False,
                    notes=f"Extracted from document source: {item.source}"
                )
                db.add(answer)
                created_count += 1

        db.commit()

        print(f"Created {created_count} answers from document sources")

        # Summary
        print(f"\n=== DOCUMENT-ONLY PIPELINE SUMMARY ===")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print(f"Document sources used: {list(by_source.keys())}")
        print(f"Total indicators with document data: {created_count}")
        print(f"Sources excluded: it_industry_patterns, financial_sector_patterns, sustainability_patterns")
        print(f"Data type: 100% document-extracted (no patterns, no templates)")

        return {
            'success': True,
            'indicators_processed': created_count,
            'sources_used': list(by_source.keys()),
            'document_only': True
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        return {'success': False, 'error': str(e)}

    finally:
        db.close()

if __name__ == "__main__":
    # Run for Infosys Limited (ID: 46) FY2024
    result = run_document_only_pipeline(46, 2024)
    print(f"\nResult: {json.dumps(result, indent=2)}")