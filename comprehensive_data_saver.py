#!/usr/bin/env python3
"""
COMPREHENSIVE DATA SOURCES SAVER
Save all data sources and scraping methods for ALL company-year combinations
Query and manage saved data sources by company and year
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
from data_source_tracker import DataSourceTracker

class ComprehensiveDataSourceSaver:
    """Save and manage data sources for all company-year combinations"""

    def __init__(self):
        self.tracker = DataSourceTracker()
        self.master_index_file = Path("data_sources_tracking/master_index.json")
        self.load_master_index()

    def load_master_index(self):
        """Load or create master index of all saved data sources"""
        if self.master_index_file.exists():
            with open(self.master_index_file, 'r') as f:
                self.master_index = json.load(f)
        else:
            self.master_index = {
                'created_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'companies': {},
                'total_company_years': 0,
                'total_companies': 0
            }

    def save_master_index(self):
        """Save master index to file"""
        self.master_index['last_updated'] = datetime.now().isoformat()
        with open(self.master_index_file, 'w') as f:
            json.dump(self.master_index, f, indent=2)

    def get_all_company_years_with_data(self) -> List[Tuple[int, str, int]]:
        """Get all company-year combinations that have data"""
        db = get_session()
        try:
            # Get all companies with scraped data
            companies_with_data = db.query(Company.id, Company.name).join(
                ScrapedData, Company.id == ScrapedData.company_id
            ).distinct().all()

            company_years = []
            for company_id, company_name in companies_with_data:
                # Get all years with data for this company
                years = db.query(ScrapedData.year).filter_by(
                    company_id=company_id
                ).distinct().all()

                for year_tuple in years:
                    year = year_tuple[0]
                    if year:  # Skip None years
                        company_years.append((company_id, company_name, year))

            return sorted(company_years, key=lambda x: (x[1], x[2]))  # Sort by name, then year

        finally:
            db.close()

    def save_all_company_year_data_sources(self, force_refresh: bool = False):
        """Save data sources for ALL company-year combinations"""
        print("[COMPREHENSIVE SAVER] Saving data sources for ALL company-year combinations")
        print("=" * 100)

        company_years = self.get_all_company_years_with_data()
        print(f"Found {len(company_years)} company-year combinations with data")

        total_saved = 0
        total_skipped = 0
        total_errors = 0

        for i, (company_id, company_name, year) in enumerate(company_years, 1):
            try:
                print(f"\n[{i:3d}/{len(company_years)}] Processing {company_name} - {year}")

                # Check if already saved (unless force refresh)
                company_key = str(company_id)
                year_key = str(year)

                if not force_refresh and company_key in self.master_index['companies']:
                    if year_key in self.master_index['companies'][company_key]['years']:
                        print(f"    [SKIP] Already saved")
                        total_skipped += 1
                        continue

                # Get data sources summary
                summary = self.tracker.get_company_year_data_sources(company_id, year)

                if 'error' in summary:
                    print(f"    [ERROR] {summary['error']}")
                    total_errors += 1
                    continue

                # Save detailed report
                report_path = self.tracker.save_data_sources_report(company_id, year, summary)

                # Update master index
                if company_key not in self.master_index['companies']:
                    self.master_index['companies'][company_key] = {
                        'company_name': company_name,
                        'years': {}
                    }

                self.master_index['companies'][company_key]['years'][year_key] = {
                    'saved_date': datetime.now().isoformat(),
                    'total_indicators': summary['total_indicators'],
                    'total_sources': summary['total_sources'],
                    'coverage_percent': summary['coverage_analysis']['target_151_coverage'],
                    'data_quality': summary['coverage_analysis']['data_quality'],
                    'report_file': Path(report_path).name
                }

                print(f"    [SAVED] {summary['total_indicators']} indicators, {summary['total_sources']} sources")
                total_saved += 1

            except Exception as e:
                print(f"    [ERROR] Failed to process: {str(e)}")
                total_errors += 1

        # Update master index totals
        self.master_index['total_company_years'] = total_saved + total_skipped
        self.master_index['total_companies'] = len(self.master_index['companies'])
        self.save_master_index()

        print(f"\n" + "=" * 100)
        print(f"[COMPREHENSIVE SAVE COMPLETE]")
        print(f"Total Saved: {total_saved}")
        print(f"Total Skipped: {total_skipped}")
        print(f"Total Errors: {total_errors}")
        print(f"Master Index: {self.master_index_file}")

    def query_by_company(self, company_name: str) -> Dict:
        """Query data sources by company name"""
        print(f"[QUERY BY COMPANY] Searching for: {company_name}")
        print("-" * 60)

        matches = {}
        for company_id, company_data in self.master_index['companies'].items():
            if company_name.lower() in company_data['company_name'].lower():
                matches[company_id] = company_data

        if not matches:
            print(f"No companies found matching '{company_name}'")
            return {}

        for company_id, company_data in matches.items():
            print(f"\nCompany: {company_data['company_name']} (ID: {company_id})")
            print(f"Years with data: {len(company_data['years'])}")

            for year, year_data in company_data['years'].items():
                print(f"  {year}: {year_data['total_indicators']} indicators, "
                      f"{year_data['coverage_percent']} coverage, "
                      f"{year_data['data_quality']} quality")

        return matches

    def query_by_year(self, year: int) -> Dict:
        """Query data sources by year"""
        print(f"[QUERY BY YEAR] Searching for year: {year}")
        print("-" * 60)

        year_key = str(year)
        matches = {}

        for company_id, company_data in self.master_index['companies'].items():
            if year_key in company_data['years']:
                matches[company_id] = {
                    'company_name': company_data['company_name'],
                    'year_data': company_data['years'][year_key]
                }

        if not matches:
            print(f"No data found for year {year}")
            return {}

        print(f"Found {len(matches)} companies with data for year {year}:")
        for company_id, data in matches.items():
            year_data = data['year_data']
            print(f"  {data['company_name']}: {year_data['total_indicators']} indicators, "
                  f"{year_data['coverage_percent']} coverage")

        return matches

    def get_data_source_statistics(self):
        """Get comprehensive statistics about all saved data sources"""
        print("[DATA SOURCE STATISTICS]")
        print("=" * 80)

        total_indicators = 0
        coverage_stats = {'EXCELLENT': 0, 'GOOD': 0, 'PARTIAL': 0}
        year_stats = {}

        for company_id, company_data in self.master_index['companies'].items():
            for year, year_data in company_data['years'].items():
                total_indicators += year_data['total_indicators']
                coverage_stats[year_data['data_quality']] += 1

                if year not in year_stats:
                    year_stats[year] = 0
                year_stats[year] += 1

        print(f"Total Companies: {self.master_index['total_companies']}")
        print(f"Total Company-Years: {self.master_index['total_company_years']}")
        print(f"Total Indicators Tracked: {total_indicators:,}")

        print(f"\nData Quality Distribution:")
        for quality, count in coverage_stats.items():
            print(f"  {quality}: {count} company-years")

        print(f"\nYear Distribution:")
        for year in sorted(year_stats.keys()):
            print(f"  {year}: {year_stats[year]} companies")

def main():
    """Main function for comprehensive data source management"""
    saver = ComprehensiveDataSourceSaver()

    print("[COMPREHENSIVE DATA SOURCE SAVER]")
    print("Save and query data sources for any company-year combination")
    print("=" * 100)

    # Option 1: Save all company-year data sources
    print("\n[OPTION 1] Save ALL company-year data sources")
    response = input("Save all company-year data sources? (y/n): ").strip().lower()
    if response == 'y':
        saver.save_all_company_year_data_sources()

    # Option 2: Query by company
    print("\n[OPTION 2] Query by company name")
    company_name = input("Enter company name (or part of name): ").strip()
    if company_name:
        saver.query_by_company(company_name)

    # Option 3: Query by year
    print("\n[OPTION 3] Query by year")
    year_input = input("Enter year: ").strip()
    if year_input.isdigit():
        saver.query_by_year(int(year_input))

    # Statistics
    print("\n[STATISTICS] Overall data source statistics")
    saver.get_data_source_statistics()

if __name__ == "__main__":
    main()