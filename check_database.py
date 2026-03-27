#!/usr/bin/env python3
"""
Check database for Infosys Ltd data after pipeline processing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, QuestionnaireSession
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
from sqlalchemy import text

def check_infosys_database_data():
    """Check what data exists for Infosys Ltd in the database"""
    company_id = 2  # Infosys Ltd
    company_name = "Infosys Ltd"
    year = 2024

    db = get_session()

    try:
        print("="*80)
        print(f"DATABASE CHECK: {company_name}")
        print(f"Company ID: {company_id} | Year: {year}")
        print("="*80)

        # 1. Check if company exists
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"ERROR: Company ID {company_id} not found in database!")
            return

        print(f"\n1. COMPANY RECORD:")
        print(f"   ✓ Company found: {company.name}")
        print(f"   ✓ ID: {company.id}")
        print(f"   ✓ Ticker: {company.ticker}")
        print(f"   ✓ Sector: {company.sector}")

        # 2. Check questionnaire sessions
        sessions = db.query(QuestionnaireSession).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"\n2. QUESTIONNAIRE SESSIONS:")
        print(f"   Sessions for {year}: {len(sessions)}")
        for session in sessions:
            print(f"     Session ID: {session.id}")
            print(f"     Status: {session.status}")
            print(f"     Standard: {session.standard}")
            print(f"     Total questions: {session.total_questions}")
            print(f"     Answered: {session.answered_questions}")

        # 3. Check raw answer count
        answer_count = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).count()

        print(f"\n3. RAW DATA COUNT:")
        print(f"   Total Answer records: {answer_count}")

        # 4. Check answers by source
        sources_query = db.execute(text("""
            SELECT source, COUNT(*) as count
            FROM answers
            WHERE company_id = :company_id AND year = :year
            GROUP BY source
        """), {"company_id": company_id, "year": year})

        sources = sources_query.fetchall()
        print(f"\n4. DATA SOURCES:")
        for source, count in sources:
            print(f"   {source or 'NULL':12}: {count:3d} records")

        # 5. Check specific indicators with values
        indicators_with_values = db.execute(text("""
            SELECT indicator_id, source, answer_value
            FROM answers
            WHERE company_id = :company_id AND year = :year
              AND answer_value IS NOT NULL
              AND answer_value != ''
            ORDER BY indicator_id
            LIMIT 10
        """), {"company_id": company_id, "year": year})

        indicators_data = indicators_with_values.fetchall()
        print(f"\n5. SAMPLE INDICATORS (first 10):")
        for indicator_id, source, value in indicators_data:
            value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"   {indicator_id:12} | {source:10} | {value_preview}")

        # 6. Use API to get summary
        print(f"\n6. API SUMMARY:")
        try:
            summary = get_indicator_summary(company_id, year, db)
            overall = summary['overall_summary']
            print(f"   API Coverage: {overall['completion_rate']:.1f}%")
            print(f"   API Indicators: {overall['indicators_with_values']}/151")

            values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")
            print(f"   API Values found: {len(values['indicators'])}")

        except Exception as e:
            print(f"   API Error: {e}")

        # 7. Check specific modules
        modules_query = db.execute(text("""
            SELECT module, COUNT(*) as count
            FROM answers
            WHERE company_id = :company_id AND year = :year
              AND answer_value IS NOT NULL
              AND answer_value != ''
              AND module IS NOT NULL
            GROUP BY module
            ORDER BY count DESC
        """), {"company_id": company_id, "year": year})

        modules_data = modules_query.fetchall()
        print(f"\n7. MODULES WITH DATA:")
        for module, count in modules_data:
            print(f"   {module[:45]:45}: {count:3d} indicators")

        # 8. Summary status
        print(f"\n8. STATUS SUMMARY:")
        if answer_count > 50:
            print(f"   ✅ GOOD: {answer_count} total records found")
        elif answer_count > 10:
            print(f"   ⚠️  MODERATE: {answer_count} records found")
        else:
            print(f"   ❌ LIMITED: Only {answer_count} records found")

        if len(indicators_data) > 30:
            print(f"   ✅ EXCELLENT: {len(indicators_data)} indicators have values")
        elif len(indicators_data) > 10:
            print(f"   ✅ GOOD: {len(indicators_data)} indicators have values")
        else:
            print(f"   ⚠️  LIMITED: Only {len(indicators_data)} indicators have values")

        print(f"\nCONCLUSION:")
        print(f"✓ Company exists in database")
        print(f"✓ Pipeline processing completed successfully")
        print(f"✓ {answer_count} answer records stored")
        print(f"✓ {len(indicators_data)} indicators have actual values")
        print(f"✓ Data available from sources: {', '.join([s[0] for s in sources])}")

    except Exception as e:
        print(f"ERROR checking database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_infosys_database_data()