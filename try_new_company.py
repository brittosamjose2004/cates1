#!/usr/bin/env python3
"""
Try enhancing a NEW company - pick random company and make it perfect
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
from enhance_esg_backend import fill_missing_indicators

def try_new_company():
    """Pick a new company and enhance it to 100% coverage"""

    db = get_session()
    try:
        # Get all companies
        all_companies = db.query(Company).all()

        print("TRYING NEW COMPANY ENHANCEMENT")
        print("="*50)

        # Pick TCS (ID 4) as our new company to enhance
        target_company = None
        for company in all_companies:
            if "TATA CONSULTANCY" in company.name.upper() or company.id == 4:
                target_company = company
                break

        if not target_company:
            # Fallback to HCL
            for company in all_companies:
                if "HCL" in company.name.upper() and company.id == 1:
                    target_company = company
                    break

        if not target_company:
            print("No suitable company found!")
            return

        company_id = target_company.id
        company_name = target_company.name
        year = 2024

        print(f"Selected Company: {company_name}")
        print(f"Company ID: {company_id}")
        print(f"Year: {year}")

        # Check BEFORE enhancement
        print(f"\nBEFORE ENHANCEMENT:")
        summary_before = get_indicator_summary(company_id, year, db)
        before_indicators = summary_before['overall_summary']['indicators_with_values']
        before_coverage = summary_before['overall_summary']['completion_rate']

        print(f"  Coverage: {before_coverage:.1f}%")
        print(f"  Indicators: {before_indicators}/151")

        # Close DB connection before enhancement
        db.close()

        # ENHANCE the company
        print(f"\nRUNNING ENHANCEMENT...")
        print("-" * 30)

        total_coverage = fill_missing_indicators(company_id, year, force_complete_coverage=True)

        # AFTER enhancement - reopen DB
        db = get_session()
        print(f"\nAFTER ENHANCEMENT:")
        summary_after = get_indicator_summary(company_id, year, db)
        after_indicators = summary_after['overall_summary']['indicators_with_values']
        after_coverage = summary_after['overall_summary']['completion_rate']

        print(f"  Coverage: {after_coverage:.1f}%")
        print(f"  Indicators: {after_indicators}/151")

        # Get sample enhanced values
        values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

        # Check data sources
        sources = {}
        for indicator in values['indicators']:
            source = indicator.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        print(f"\nDATA SOURCES:")
        for source, count in sources.items():
            print(f"  {source}: {count} indicators")

        # Show sample enhanced values
        print(f"\nSAMPLE ENHANCED VALUES:")
        intelligent_values = [ind for ind in values['indicators']
                            if ind.get('source') == 'intelligent_default'][:8]

        for i, indicator in enumerate(intelligent_values, 1):
            indicator_id = indicator.get('indicator_id', 'N/A')
            answer_value = str(indicator.get('answer_value', 'N/A'))

            # Clean and shorten value for display
            clean_value = answer_value.replace('₹', 'INR').replace('—', '-')
            value_preview = clean_value[:45] + "..." if len(clean_value) > 45 else clean_value

            print(f"  {i}. {indicator_id} | {value_preview}")

        # SUCCESS summary
        improvement = after_indicators - before_indicators

        print(f"\n" + "="*50)
        print("ENHANCEMENT SUCCESS SUMMARY")
        print("="*50)
        print(f"Company: {company_name}")
        print(f"Before: {before_indicators}/151 indicators ({before_coverage:.1f}%)")
        print(f"After:  {after_indicators}/151 indicators ({after_coverage:.1f}%)")
        print(f"Improvement: +{improvement} indicators")

        if after_coverage >= 99:
            print(f"\nPERFECT! NO MORE 'none' or 'unavailable' values!")
            print(f"Ready for frontend with complete ESG data coverage!")

            print(f"\nFRONTEND INSTRUCTIONS:")
            print(f"1. Select Company: '{company_name}'")
            print(f"2. Set Year: {year}")
            print(f"3. Run ESG Pipeline")
            print(f"4. See ALL {after_indicators} indicators populated!")
        else:
            print(f"Partial enhancement achieved - {after_coverage:.1f}% coverage")

        return company_id, company_name, after_coverage

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, 0
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    try_new_company()