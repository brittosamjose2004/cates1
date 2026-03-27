#!/usr/bin/env python3
"""
FILL ALL 151 INDICATORS - ANY COMPANY
Simple command to fill all 151 ESG indicators for any company with 100% coverage
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from complete_151_all_indicators import fill_all_151_indicators
from backend.database.db import get_session
from backend.database.models import Company

def fill_any_company(company_id, year=2024):
    """Fill all 151 indicators for any company - guaranteed 100% coverage"""
    result = fill_all_151_indicators(company_id, year)
    return result

def list_all_companies():
    """Show all available companies"""
    db = get_session()
    try:
        companies = db.query(Company).all()
        print(f"\nAVAILABLE COMPANIES ({len(companies)} total):")
        print("=" * 50)
        for company in companies:
            print(f"ID: {company.id:2d} | {company.name}")
        return companies
    finally:
        db.close()

def fill_all_companies(year=2024):
    """Fill all 151 indicators for ALL companies"""
    db = get_session()
    try:
        companies = db.query(Company).all()
        print(f"FILLING ALL 151 INDICATORS FOR ALL {len(companies)} COMPANIES")
        print("=" * 70)

        success_count = 0

        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] Processing: {company.name}")
            result = fill_all_151_indicators(company.id, year, db_session=db)

            if result == 151:
                success_count += 1
                print(f"✅ SUCCESS: {result}/151 indicators")
            else:
                print(f"⚠️ PARTIAL: {result}/151 indicators")

        print(f"\n" + "=" * 70)
        print(f"FINAL SUMMARY:")
        print(f"✅ {success_count}/{len(companies)} companies have 100% coverage")
        print(f"📊 Total companies processed: {len(companies)}")
        print(f"🎯 Success rate: {(success_count/len(companies))*100:.1f}%")

        return success_count

    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Fill ALL 151 ESG Indicators for ANY Company")
    parser.add_argument("--company_id", type=int, help="Specific company ID to fill")
    parser.add_argument("--list", action="store_true", help="List all available companies")
    parser.add_argument("--all", action="store_true", help="Fill ALL companies")
    parser.add_argument("--year", type=int, default=2024, help="Year (default: 2024)")

    args = parser.parse_args()

    if args.list:
        companies = list_all_companies()
        print(f"\nUsage examples:")
        print(f"python fill_any_company.py --company_id=1    # Fill specific company")
        print(f"python fill_any_company.py --all             # Fill ALL companies")
        return

    if args.all:
        print("Filling ALL companies with 151 indicators each...")
        success_count = fill_all_companies(args.year)
        print(f"\nCompleted: {success_count} companies successfully filled")
        return

    if args.company_id:
        print(f"Filling company {args.company_id} with ALL 151 indicators...")
        result = fill_any_company(args.company_id, args.year)

        if result == 151:
            print(f"\n🎉 SUCCESS! Company {args.company_id} now has ALL 151 indicators filled!")
        else:
            print(f"\n⚠️ PARTIAL: {result}/151 indicators filled for company {args.company_id}")
        return

    # No arguments - show help
    print("🎯 FILL ALL 151 INDICATORS - ANY COMPANY")
    print("=" * 50)
    print("Usage:")
    print("  --list              Show all companies")
    print("  --company_id=X      Fill specific company")
    print("  --all               Fill ALL companies")
    print("  --year=YYYY         Specify year (default: 2024)")
    print("\nExamples:")
    print("  python fill_any_company.py --list")
    print("  python fill_any_company.py --company_id=1")
    print("  python fill_any_company.py --all")

if __name__ == "__main__":
    main()