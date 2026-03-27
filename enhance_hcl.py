#!/usr/bin/env python3
"""
Try enhancing HCL Technologies - another new company
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company
from backend.api.routers.indicators import get_indicator_summary
from enhance_esg_backend import fill_missing_indicators

def enhance_hcl():
    """Enhance HCL Technologies"""

    company_id = 1  # HCL Technologies Ltd
    year = 2024

    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()

        print("ENHANCING HCL TECHNOLOGIES")
        print("="*40)
        print(f"Company: {company.name}")

        # Before
        summary_before = get_indicator_summary(company_id, year, db)
        before = summary_before['overall_summary']['indicators_with_values']

        print(f"Before: {before}/151 indicators")

        db.close()

        # Enhance
        fill_missing_indicators(company_id, year, force_complete_coverage=True)

        # After
        db = get_session()
        summary_after = get_indicator_summary(company_id, year, db)
        after = summary_after['overall_summary']['indicators_with_values']

        print(f"After: {after}/151 indicators")
        print(f"SUCCESS: +{after-before} indicators added!")

        if after >= 150:
            print("PERFECT! Ready for frontend with NO 'none' values!")

    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    enhance_hcl()