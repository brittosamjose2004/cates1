#!/usr/bin/env python3
"""
Quick database check for Infosys Ltd (from job_147.log)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer
from sqlalchemy import func

def quick_infosys_check():
    """Quick check for Infosys data in database"""
    company_id = 2  # Infosys Ltd
    year = 2024

    db = get_session()
    try:
        print("QUICK DATABASE CHECK - Infosys Ltd")
        print("=" * 50)

        # 1. Company exists?
        company = db.query(Company).filter_by(id=company_id).first()
        if company:
            print(f"Company found: {company.name} (ID: {company_id})")
        else:
            print(f"Company ID {company_id} NOT FOUND")
            return

        # 2. Answer count
        total_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).count()
        print(f"Total answer records: {total_answers}")

        # 3. Answers with values
        valued_answers = db.query(Answer).filter(
            Answer.company_id == company_id,
            Answer.year == year,
            Answer.answer_value.isnot(None),
            Answer.answer_value != ''
        ).count()
        print(f"Answers with values: {valued_answers}")

        # 4. Source breakdown
        sources = db.query(
            Answer.source,
            func.count(Answer.id)
        ).filter_by(
            company_id=company_id,
            year=year
        ).group_by(Answer.source).all()

        print(f"Data sources:")
        for source, count in sources:
            print(f"  - {source or 'NULL'}: {count} records")

        # 5. Sample indicators
        samples = db.query(Answer).filter(
            Answer.company_id == company_id,
            Answer.year == year,
            Answer.answer_value.isnot(None),
            Answer.answer_value != ''
        ).limit(5).all()

        print(f"Sample indicators:")
        for answer in samples:
            value_preview = str(answer.answer_value)[:40] + "..." if len(str(answer.answer_value)) > 40 else str(answer.answer_value)
            print(f"  - {answer.indicator_id}: {value_preview}")

        # Summary
        print("\nSUMMARY:")
        if valued_answers >= 50:
            print(f"EXCELLENT: {valued_answers} indicators with data")
        elif valued_answers >= 20:
            print(f"GOOD: {valued_answers} indicators with data")
        elif valued_answers >= 5:
            print(f"MODERATE: {valued_answers} indicators with data")
        else:
            print(f"LIMITED: Only {valued_answers} indicators with data")

        print(f"\nRECOMMENDATION:")
        if valued_answers >= 20:
            print(f"Use 'Infosys Ltd' in frontend - good data coverage!")
        else:
            print(f"Consider using 'COMPREHENSIVE ESG TEST COMPANY' instead")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    quick_infosys_check()