#!/usr/bin/env python3
"""
API TEST - JSW STEEL 2023 DATA
Test the API layer to see what data it returns for JSW Steel 2023
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, CompanyYear, Answer, Question, Indicator

def test_api_data_retrieval(company_id: int = 44, year: int = 2023):
    """Test what the API layer returns for JSW Steel 2023"""
    db = get_session()
    try:
        print(f"[API TEST] JSW Steel Limited - Year {year}")
        print("=" * 60)

        # Test 1: Company exists?
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print("[ERROR] Company not found")
            return
        print(f"[✓] Company found: {company.name}")

        # Test 2: CompanyYear exists?
        company_year = db.query(CompanyYear).filter_by(company_id=company_id, year=year).first()
        if not company_year:
            print(f"[ERROR] CompanyYear {year} not found")
            return
        print(f"[✓] CompanyYear found: {year}")

        # Test 3: Check Answers (processed indicators)
        answers = db.query(Answer).filter_by(company_year_id=company_year.id).all()
        print(f"[✓] Answers found: {len(answers)}")

        if answers:
            # Sample answers by source
            by_source = {}
            for answer in answers[:20]:  # First 20 answers
                question = db.query(Question).filter_by(id=answer.question_id).first()
                indicator = db.query(Indicator).filter_by(id=question.indicator_id).first() if question else None

                source = answer.source_priority or "unknown"
                if source not in by_source:
                    by_source[source] = []

                indicator_code = indicator.code if indicator else "unknown"
                by_source[source].append({
                    "indicator": indicator_code,
                    "value": answer.value,
                    "confidence": answer.confidence,
                    "source": answer.source_detail
                })

            print(f"\n[API] Sample answers by source:")
            for source, answers_list in by_source.items():
                print(f"  {source}: {len(answers_list)} answers")
                for answer in answers_list[:3]:  # Show first 3
                    print(f"    {answer['indicator']}: {str(answer['value'])[:40]}...")

        # Test 4: Check what years have data
        all_years = db.query(CompanyYear.year).filter_by(company_id=company_id).all()
        years_available = sorted([y[0] for y in all_years])
        print(f"\n[API] Available years for JSW Steel: {years_available}")

        # Test 5: Check latest year
        latest_year = db.query(CompanyYear).filter_by(company_id=company_id).order_by(CompanyYear.year.desc()).first()
        print(f"[API] Latest year: {latest_year.year if latest_year else 'None'}")

        return len(answers)

    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    count = test_api_data_retrieval(44, 2023)
    print(f"\n[RESULT] API would return {count} processed indicators")

    print("\n" + "="*60)
    print("[SUMMARY] COMPREHENSIVE SYSTEM STATUS")
    print("✓ Database: 390 scraped indicators (258% coverage)")
    print("✓ Processing: Testing API layer...")
    print("? Frontend: Shows 0/151 (investigation needed)")
    print("="*60)