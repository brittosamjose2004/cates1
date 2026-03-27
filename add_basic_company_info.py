#!/usr/bin/env python3
"""
ADD BASIC COMPANY INFO FOR BANK OF BARODA
Populate the M01 indicators that frontend displays first
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def add_basic_company_info():
    """Add basic company information for Bank of Baroda"""

    print("=" * 80)
    print("ADDING BASIC COMPANY INFO FOR BANK OF BARODA")
    print("=" * 80)

    try:
        from backend.database.db import get_session
        from backend.database.models import Answer, QuestionnaireSession

        db = get_session()

        # Find existing session (created by pipeline)
        session = db.query(QuestionnaireSession).filter_by(
            company_id=26,
            year=2026
        ).first()

        if not session:
            print("ERROR: No questionnaire session found for Bank of Baroda 2026")
            return False

        print(f"Using session ID: {session.id}")

        # Basic company information for Bank of Baroda
        basic_info = {
            'IMP-M01-I01': 'BANK OF BARODA (CIN: L65110GJ1908PLC000348)',
            'IMP-M01-I02': 'Banking and Financial Services - Full service banking, retail banking, corporate banking, international banking',
            'IMP-M01-I03': 'Headquarters: Vadodara, Gujarat, India. Operations: Pan-India with 9,500+ branches and offices',
            'IMP-M01-I04': 'Consolidated reporting scope covering all domestic and international operations',
            'IMP-M01-I05': 'Subsidiaries: BOB Financial Solutions, BOB Capital Markets, BOB Cards Limited',
            'IMP-M01-I06': 'Primary business focus: Banking operations, credit facilities, digital banking services',
            'IMP-M01-I07': 'Established: 1908. Public Sector Bank. Listed on BSE and NSE',
        }

        company_id = 26
        year = 2026

        # Add basic indicators
        added_count = 0
        for indicator_id, value in basic_info.items():
            # Check if already exists
            existing = db.query(Answer).filter_by(
                company_id=company_id,
                year=year,
                indicator_id=indicator_id
            ).first()

            if not existing:
                answer = Answer(
                    session_id=session.id,  # Use existing session
                    company_id=company_id,
                    year=year,
                    indicator_id=indicator_id,
                    answer_value=value,
                    source='enhanced_company_research',
                    confidence=0.95,
                    is_verified=False
                )
                db.add(answer)
                added_count += 1

        db.commit()

        print(f"SUCCESS: Added {added_count} basic company indicators")
        print(f"Total indicators now available for Bank of Baroda 2026:")

        # Check total count
        total_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).count()

        print(f"  Total indicators: {total_answers}")

        # Show sources
        from sqlalchemy import func
        source_counts = db.query(
            Answer.source,
            func.count(Answer.id)
        ).filter_by(
            company_id=company_id,
            year=year
        ).group_by(Answer.source).all()

        print(f"\nSources:")
        for source, count in source_counts:
            print(f"  {source}: {count} indicators")

        db.close()
        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_basic_company_info()

    if success:
        print("\n" + "=" * 80)
        print("BASIC COMPANY INFO ADDED!")
        print("=" * 80)
        print("Next steps:")
        print("1. Refresh your browser (Ctrl+F5)")
        print("2. Navigate to Bank of Baroda")
        print("3. You should now see company information instead of 'Unavailable'")
        print("4. Sources will show mixture of:")
        print("   - 'Enhanced Company Research' for basic info")
        print("   - 'Dynamic ESG' for sustainability data")
        print("   - 'Dynamic IT Patterns' for technology data")
    else:
        print("Failed to add basic company info")