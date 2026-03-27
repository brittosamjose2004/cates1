#!/usr/bin/env python3
"""
DATA SOURCES DEMO - Show and Save Company-Year Data Sources
Demonstrate the data source tracking and saving system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from comprehensive_data_saver import ComprehensiveDataSourceSaver
from data_source_tracker import DataSourceTracker

def demo_data_source_tracking():
    """Demonstrate data source tracking and saving for company-year combinations"""
    print("[DEMO] DATA SOURCES TRACKING AND SAVING")
    print("Show what data and scraping is used for each company-year combination")
    print("=" * 100)

    tracker = DataSourceTracker()
    saver = ComprehensiveDataSourceSaver()

    # Demo 1: Show JSW Steel 2023 data sources in detail
    print("\n[DEMO 1] JSW Steel Limited 2023 - Detailed Data Sources")
    print("-" * 80)
    summary = tracker.display_data_sources_summary(44, 2023)

    # Demo 2: Show what companies and years have data
    print("\n\n[DEMO 2] All Companies and Years with Data")
    print("-" * 80)
    company_years = saver.get_all_company_years_with_data()

    print(f"Found {len(company_years)} company-year combinations with data:")
    current_company = None
    for company_id, company_name, year in company_years[:15]:  # Show first 15
        if company_name != current_company:
            if current_company is not None:
                print()  # New line between companies
            current_company = company_name
            print(f"{company_name} (ID: {company_id}):")

        print(f"  Year {year}: Available")

    if len(company_years) > 15:
        print(f"... and {len(company_years) - 15} more company-year combinations")

    # Demo 3: Save data sources for selected companies
    print("\n\n[DEMO 3] Saving Data Sources for Key Companies")
    print("-" * 80)

    # Save for JSW Steel and a few other companies with good data
    key_companies = [
        (44, "JSW Steel Limited"),
        (14, "Asian Paints"),
        (1, "HCL Technologies"),
        (4, "Tata Consultancy Services")
    ]

    for company_id, company_name in key_companies:
        print(f"\nSaving data sources for {company_name}...")

        # Find years with data for this company
        company_years_data = [cy for cy in company_years if cy[0] == company_id]

        for _, _, year in company_years_data[:2]:  # Save for first 2 years
            try:
                summary = tracker.get_company_year_data_sources(company_id, year)
                if 'error' not in summary:
                    report_path = tracker.save_data_sources_report(company_id, year, summary)
                    print(f"  {year}: Saved {summary['total_indicators']} indicators from {summary['total_sources']} sources")
                else:
                    print(f"  {year}: Error - {summary['error']}")
            except Exception as e:
                print(f"  {year}: Failed - {str(e)}")

    # Demo 4: Query saved data sources
    print("\n\n[DEMO 4] Query Saved Data Sources")
    print("-" * 80)

    # Query by company
    print("\nQuerying by company name 'JSW':")
    saver.query_by_company("JSW")

    # Query by year
    print(f"\nQuerying by year 2023:")
    saver.query_by_year(2023)

def show_data_source_file_contents():
    """Show the contents of a saved data source file"""
    print("\n\n[DEMO 5] Sample Saved Data Source File Contents")
    print("-" * 80)

    # Look for JSW Steel 2023 file
    data_sources_dir = Path("data_sources_tracking")
    jsw_file = data_sources_dir / "JSW_Steel_Limited_2023_data_sources.json"

    if jsw_file.exists():
        import json
        with open(jsw_file, 'r') as f:
            data = json.load(f)

        print(f"File: {jsw_file.name}")
        print(f"Company: {data['company_name']}")
        print(f"Year: {data['year']}")
        print(f"Total Indicators: {data['total_indicators']}")
        print(f"Total Sources: {data['total_sources']}")

        print(f"\nData Sources Used:")
        for source_name, source_data in data['source_breakdown'].items():
            print(f"  {source_name}:")
            print(f"    Type: {source_data['type']}")
            print(f"    Indicators: {source_data['indicator_count']}")

        print(f"\nScraping/Collection Methods:")
        for method, sources in data['source_methods'].items():
            if sources:
                print(f"  {method.replace('_', ' ').title()}: {sources}")

        print(f"\nCoverage Analysis:")
        coverage = data['coverage_analysis']
        print(f"  Target 151 Coverage: {coverage['target_151_coverage']}")
        print(f"  Data Quality: {coverage['data_quality']}")
    else:
        print(f"File not found: {jsw_file}")
        print("Run the demo first to create the file")

if __name__ == "__main__":
    # Run the demo
    demo_data_source_tracking()

    # Show file contents
    show_data_source_file_contents()

    print("\n" + "=" * 100)
    print("[DEMO COMPLETE]")
    print("✅ Data sources tracked and saved for company-year combinations")
    print("✅ Files saved in: data_sources_tracking/")
    print("✅ Query by company name or year")
    print("✅ Master index tracks all saved data sources")
    print("=" * 100)