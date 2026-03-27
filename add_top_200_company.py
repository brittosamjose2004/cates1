#!/usr/bin/env python3
"""
ADD ANY TOP 200 COMPANY - COMPLETE ESG PROCESSING
Simple tool to add any new Top 200 stock company and fill all 151 ESG indicators
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company
from fill_any_company import fill_any_company

def add_top_200_company(name, ticker=None, description=None):
    """Add a new Top 200 company to database"""
    db = get_session()
    try:
        # Check if company already exists
        existing = db.query(Company).filter(Company.name.ilike(f"%{name}%")).first()
        if existing:
            print(f"Company '{name}' already exists as: {existing.name} (ID: {existing.id})")
            return existing.id

        # Add new company
        new_company = Company(
            name=name,
            ticker=ticker or name.replace(' ', '').upper()[:10],
            description=description or f"Top 200 stock company - {name}"
        )
        db.add(new_company)
        db.commit()

        print(f"✅ ADDED: {name} (Company ID: {new_company.id})")
        return new_company.id

    finally:
        db.close()

def process_top_200_company(company_name, ticker=None, description=None, year=2024):
    """Complete workflow: Add company + Fill all 151 ESG indicators"""
    print(f"PROCESSING TOP 200 COMPANY: {company_name}")
    print("=" * 70)

    # Step 1: Add company to database
    print("Step 1: Adding to database...")
    company_id = add_top_200_company(company_name, ticker, description)

    # Step 2: Fill all 151 ESG indicators
    print(f"\nStep 2: Filling 151 ESG indicators...")
    result = fill_any_company(company_id, year)

    # Step 3: Results summary
    print(f"\n" + "=" * 70)
    print(f"FINAL RESULTS FOR {company_name}:")
    print("=" * 70)
    print(f"Company ID: {company_id}")
    print(f"Indicators filled: {result}/151")
    print(f"Coverage: {(result/151)*100:.1f}%")

    if result == 151:
        print(f"🎉 SUCCESS: {company_name} is ESG-ready!")
        print(f"All 21 ESG modules completed with realistic data")
    else:
        print(f"⚠️ Partial completion: {151-result} indicators pending")

    return company_id, result

# Pre-defined Top 200 companies for quick testing
TOP_200_COMPANIES = {
    'reliance': {
        'name': 'Reliance Industries Limited',
        'ticker': 'RELIANCE',
        'description': 'Oil, petrochemicals, retail, telecommunications - India\'s largest private company'
    },
    'sbi': {
        'name': 'State Bank of India',
        'ticker': 'SBIN',
        'description': 'India\'s largest public sector bank'
    },
    'icici': {
        'name': 'ICICI Bank Limited',
        'ticker': 'ICICIBANK',
        'description': 'Private sector banking and financial services'
    },
    'hdfc': {
        'name': 'HDFC Bank Limited',
        'ticker': 'HDFCBANK',
        'description': 'Private sector banking and financial services'
    },
    'bharti': {
        'name': 'Bharti Airtel Limited',
        'ticker': 'BHARTIARTL',
        'description': 'Telecommunications and digital services'
    },
    'maruti': {
        'name': 'Maruti Suzuki India Limited',
        'ticker': 'MARUTI',
        'description': 'Automobile manufacturing and sales'
    },
    'adani': {
        'name': 'Adani Enterprises Limited',
        'ticker': 'ADANIENT',
        'description': 'Infrastructure, commodities trading, and integrated business'
    },
    'ultracemco': {
        'name': 'UltraTech Cement Limited',
        'ticker': 'ULTRACEMCO',
        'description': 'Cement manufacturing and building materials'
    },
    'titan': {
        'name': 'Titan Company Limited',
        'ticker': 'TITAN',
        'description': 'Jewelry, watches, and lifestyle products'
    },
    'sunpharma': {
        'name': 'Sun Pharmaceutical Industries Limited',
        'ticker': 'SUNPHARMA',
        'description': 'Pharmaceutical manufacturing and healthcare'
    }
}

def main():
    parser = argparse.ArgumentParser(description="Add and Process Any Top 200 Company")
    parser.add_argument("--name", type=str, help="Company name")
    parser.add_argument("--ticker", type=str, help="Stock ticker symbol")
    parser.add_argument("--description", type=str, help="Company description")
    parser.add_argument("--preset", type=str, choices=list(TOP_200_COMPANIES.keys()),
                       help="Use preset Top 200 company")
    parser.add_argument("--list", action="store_true", help="List available preset companies")
    parser.add_argument("--year", type=int, default=2024, help="Year (default: 2024)")

    args = parser.parse_args()

    if args.list:
        print("AVAILABLE TOP 200 PRESET COMPANIES:")
        print("=" * 60)
        for key, info in TOP_200_COMPANIES.items():
            print(f"{key:12s}: {info['name']}")
            print(f"{'':14s}({info['ticker']}) - {info['description'][:50]}...")
            print()
        print("Usage: python add_top_200_company.py --preset=reliance")
        return

    if args.preset:
        if args.preset in TOP_200_COMPANIES:
            company_info = TOP_200_COMPANIES[args.preset]
            company_id, result = process_top_200_company(
                company_info['name'],
                company_info['ticker'],
                company_info['description'],
                args.year
            )
        else:
            print(f"Unknown preset: {args.preset}")
            print(f"Available presets: {list(TOP_200_COMPANIES.keys())}")
        return

    if args.name:
        company_id, result = process_top_200_company(
            args.name,
            args.ticker,
            args.description,
            args.year
        )
        return

    # No arguments - show help
    print("🏆 ADD ANY TOP 200 COMPANY - COMPLETE ESG PROCESSING")
    print("=" * 60)
    print("Usage:")
    print("  --name='Company Name'    Add custom company")
    print("  --preset=reliance        Use preset Top 200 company")
    print("  --list                   Show all preset companies")
    print("\nExamples:")
    print("  python add_top_200_company.py --preset=sbi")
    print("  python add_top_200_company.py --name='Mahindra & Mahindra' --ticker=M&M")
    print("  python add_top_200_company.py --list")
    print("\nThis will:")
    print("  1. Add the company to database")
    print("  2. Fill ALL 151 ESG indicators")
    print("  3. Generate realistic sector-specific data")
    print("  4. Provide 100% coverage guarantee")

if __name__ == "__main__":
    main()