#!/usr/bin/env python3
"""
Check database for NIPPON LIFE INDIA ASSET MANAGEMENT LIMITED data
Based on pipeline job 117 log
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, QuestionnaireSession
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
from sqlalchemy import text

def check_nippon_life_data():
    """Check database for NIPPON LIFE INDIA ASSET MANAGEMENT LIMITED data"""

    # From pipeline log job 117
    company_id = 39
    company_name = "NIPPON LIFE INDIA ASSET MANAGEMENT LIMITED"
    year = 2025

    db = get_session()
    try:
        print("="*80)
        print("DATABASE VERIFICATION CHECK")
        print(f"Pipeline Job: 117")
        print(f"Company: {company_name}")
        print(f"Company ID: {company_id}")
        print(f"Year: {year}")
        print("="*80)

        # 1. Check if company exists
        company = db.query(Company).filter_by(id=company_id).first()

        print(f"\n1. COMPANY EXISTENCE:")
        if company:
            print(f"   * Company found: {company.name}")
            print(f"   * Company ID: {company.id}")
            print(f"   * Status: EXISTS in database")
        else:
            print(f"   X Company ID {company_id} NOT FOUND in database!")
            print(f"   * This indicates a database sync issue")
            return

        # 2. Check total answer records
        total_answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).count()

        print(f"\n2. ANSWER RECORDS:")
        print(f"   * Total records in database: {total_answers}")
        print(f"   * Expected from pipeline: 131")

        if total_answers >= 100:
            print(f"   * Status: EXCELLENT - Good data coverage")
        elif total_answers >= 50:
            print(f"   * Status: GOOD - Moderate coverage")
        elif total_answers >= 10:
            print(f"   * Status: LIMITED - Basic coverage")
        else:
            print(f"   * Status: POOR - Very limited data")

        # 3. Check answers with actual values
        answers_with_values = db.execute(text("""
            SELECT COUNT(*)
            FROM answers
            WHERE company_id = :company_id
            AND year = :year
            AND answer_value IS NOT NULL
            AND answer_value != ''
            AND answer_value != 'N/A'
        """), {"company_id": company_id, "year": year}).fetchone()[0]

        print(f"\n3. MEANINGFUL DATA:")
        print(f"   * Records with actual values: {answers_with_values}")
        print(f"   * Empty/null records: {total_answers - answers_with_values}")

        # 4. Check data sources
        sources = db.execute(text("""
            SELECT source, COUNT(*) as count
            FROM answers
            WHERE company_id = :company_id AND year = :year
            AND answer_value IS NOT NULL
            GROUP BY source
            ORDER BY count DESC
        """), {"company_id": company_id, "year": year}).fetchall()

        print(f"\n4. DATA SOURCES:")
        for source, count in sources:
            print(f"   * {source or 'NULL':12}: {count:3d} indicators")

        # 5. Sample actual data
        sample_data = db.execute(text("""
            SELECT indicator_id, source, answer_value
            FROM answers
            WHERE company_id = :company_id AND year = :year
            AND answer_value IS NOT NULL
            AND answer_value != ''
            ORDER BY indicator_id
            LIMIT 10
        """), {"company_id": company_id, "year": year}).fetchall()

        print(f"\n5. SAMPLE DATA (first 10 non-empty):")
        if sample_data:
            for indicator_id, source, value in sample_data:
                # Clean value for safe display
                clean_value = str(value).replace('₹', 'INR').replace('—', '-')
                value_preview = clean_value[:40] + "..." if len(clean_value) > 40 else clean_value
                print(f"   * {indicator_id:12} | {source:8} | {value_preview}")
        else:
            print(f"   * No sample data found with values")

        # 6. API verification
        print(f"\n6. API VERIFICATION:")
        try:
            summary = get_indicator_summary(company_id, year, db)
            overall = summary['overall_summary']

            api_indicators = overall['indicators_with_values']
            api_coverage = overall['completion_rate']

            print(f"   * API reports: {api_indicators}/151 indicators ({api_coverage:.1f}%)")

            # Check if API matches database
            if api_indicators == answers_with_values:
                print(f"   * Status: CONSISTENT - API matches database")
            else:
                print(f"   * Status: MISMATCH - API ({api_indicators}) vs DB ({answers_with_values})")

        except Exception as e:
            print(f"   * API Error: {str(e)[:60]}")

        # 7. Module breakdown
        modules = db.execute(text("""
            SELECT module, COUNT(*) as count
            FROM answers
            WHERE company_id = :company_id AND year = :year
            AND answer_value IS NOT NULL
            AND module IS NOT NULL
            GROUP BY module
            HAVING count > 0
            ORDER BY count DESC
            LIMIT 10
        """), {"company_id": company_id, "year": year}).fetchall()

        print(f"\n7. TOP MODULES WITH DATA:")
        for module, count in modules:
            print(f"   * {module[:40]:40}: {count:2d} indicators")

        # 8. Final assessment
        print(f"\n" + "="*80)
        print("FINAL ASSESSMENT")
        print("="*80)

        print(f"Pipeline Status: SUCCESS (131 indicators processed)")
        print(f"Database Status: {'SUCCESS' if total_answers > 0 else 'FAILED'} ({total_answers} records stored)")
        print(f"Data Quality: {'GOOD' if answers_with_values >= 10 else 'POOR'} ({answers_with_values} meaningful values)")

        if total_answers > 100 and answers_with_values > 10:
            print(f"CONCLUSION: ✓ Data successfully stored and accessible")
            print(f"RECOMMENDATION: Use this company in frontend - has good ESG data coverage")
        elif total_answers > 10:
            print(f"CONCLUSION: ~ Partial data stored - some indicators available")
            print(f"RECOMMENDATION: Company has limited ESG data")
        else:
            print(f"CONCLUSION: X Minimal or no data stored")
            print(f"RECOMMENDATION: Data may not have been properly saved")

    except Exception as e:
        print(f"ERROR during database check: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_nippon_life_data()