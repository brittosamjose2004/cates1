#!/usr/bin/env python3
"""
QUICK DATA SOURCES QUERY
Simple interface to query what data sources and scraping methods are used for any company-year
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from data_source_tracker import DataSourceTracker
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def quick_query_data_sources(company_name: str = None, company_id: int = None, year: int = None):
    """Quick query for data sources used by company and year"""
    tracker = DataSourceTracker()
    db = get_session()

    try:
        # Find company if name provided
        if company_name and not company_id:
            companies = db.query(Company).filter(
                Company.name.ilike(f"%{company_name}%")
            ).all()

            if not companies:
                print(f"No companies found matching '{company_name}'")
                return
            elif len(companies) == 1:
                target_company = companies[0]
                company_id = target_company.id
                print(f"Found: {target_company.name} (ID: {company_id})")
            else:
                print(f"Multiple companies found matching '{company_name}':")
                for i, company in enumerate(companies, 1):
                    print(f"  {i}. {company.name} (ID: {company.id})")

                choice = input("Enter number to select company: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(companies):
                    target_company = companies[int(choice) - 1]
                    company_id = target_company.id
                    print(f"Selected: {target_company.name} (ID: {company_id})")
                else:
                    print("Invalid selection")
                    return

        # Find available years if not specified
        if company_id and not year:
            years = db.query(ScrapedData.year).filter_by(
                company_id=company_id
            ).distinct().all()

            available_years = sorted([y[0] for y in years if y[0]])

            if not available_years:
                print(f"No data found for company ID {company_id}")
                return
            elif len(available_years) == 1:
                year = available_years[0]
                print(f"Using year: {year}")
            else:
                print(f"Available years: {available_years}")
                year_input = input("Enter year: ").strip()
                if year_input.isdigit() and int(year_input) in available_years:
                    year = int(year_input)
                else:
                    print("Invalid year selection")
                    return

        # Get company name if we have ID
        if company_id and not company_name:
            company = db.query(Company).filter_by(id=company_id).first()
            company_name = company.name if company else f"Company {company_id}"

        print(f"\n[QUICK QUERY] Data Sources for {company_name} - Year {year}")
        print("=" * 80)

        # Get data sources summary
        summary = tracker.get_company_year_data_sources(company_id, year)

        if 'error' in summary:
            print(f"Error: {summary['error']}")
            return

        # Display concise summary
        print(f"Total Indicators: {summary['total_indicators']}")
        print(f"Target 151 Coverage: {summary['coverage_analysis']['target_151_coverage']}")
        print(f"Data Quality: {summary['coverage_analysis']['data_quality']}")
        print(f"Sources Used: {summary['total_sources']}")

        print(f"\nData Sources Breakdown:")
        for source_name, source_data in summary['source_breakdown'].items():
            print(f"  {source_name}:")
            print(f"    Type: {source_data['type'].upper()}")
            print(f"    Indicators: {source_data['indicator_count']}")

            if source_data['sample_values']:
                print(f"    Sample: {source_data['sample_values'][0]['indicator']} = {source_data['sample_values'][0]['value'][:40]}...")

        print(f"\nScraping/Collection Methods Used:")
        for method, sources in summary['source_methods'].items():
            if sources:
                method_name = method.replace('_', ' ').title()
                print(f"  {method_name}: {len(sources)} source(s)")

        return summary

    finally:
        db.close()

def interactive_query():
    """Interactive interface for querying data sources"""
    print("[INTERACTIVE DATA SOURCES QUERY]")
    print("Find out what data and scraping methods are used for any company-year")
    print("=" * 80)

    while True:
        print(f"\nOptions:")
        print(f"1. Query by company name")
        print(f"2. Query by company ID")
        print(f"3. Quick query (JSW Steel 2023)")
        print(f"4. Quick query (Asian Paints 2025)")
        print(f"5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            company_name = input("Enter company name (or part of name): ").strip()
            if company_name:
                quick_query_data_sources(company_name=company_name)

        elif choice == '2':
            company_id_input = input("Enter company ID: ").strip()
            if company_id_input.isdigit():
                quick_query_data_sources(company_id=int(company_id_input))

        elif choice == '3':
            print("\nQuick query: JSW Steel 2023")
            quick_query_data_sources(company_id=44, year=2023)

        elif choice == '4':
            print("\nQuick query: Asian Paints 2025")
            quick_query_data_sources(company_id=14, year=2025)

        elif choice == '5':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    interactive_query()