#!/usr/bin/env python3
"""
Simple database check for Infosys data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer
from backend.api.routers.indicators import get_indicator_summary

def quick_check():
    """Quick check of Infosys database data"""
    db = get_session()

    # Check Infosys (ID: 2) for 2024
    company_id = 2
    year = 2024

    try:
        # Get company
        company = db.query(Company).filter_by(id=company_id).first()
        print(f"Company: {company.name if company else 'NOT FOUND'}")

        # Count answers
        answer_count = db.query(Answer).filter_by(company_id=company_id, year=year).count()
        print(f"Answer records: {answer_count}")

        # Get summary via API
        if company:
            summary = get_indicator_summary(company_id, year, db)
            print(f"API Coverage: {summary['overall_summary']['completion_rate']:.1f}%")
            print(f"Indicators with values: {summary['overall_summary']['indicators_with_values']}")

        print("\nSTATUS: Database contains Infosys data" if answer_count > 0 else "STATUS: NO data found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    quick_check()