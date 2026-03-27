#!/usr/bin/env python3
"""
CLI Test: Top 200 Companies ESG Processing
Focus on major Indian companies from NSE Top 200 list
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company
from backend.services.company_year_processor import CompanyYearProcessor
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
import time

def find_companies_by_name(search_terms):
    """Find companies in database matching search terms"""
    db = get_session()
    try:
        found_companies = []
        all_companies = db.query(Company).all()

        for search_term in search_terms:
            for company in all_companies:
                if search_term.lower() in company.name.lower():
                    found_companies.append((company.id, company.name))
                    break

        return found_companies
    finally:
        db.close()

def test_top_200_companies():
    """Test major companies likely to be in Top 200 NSE list"""

    # Major companies from Top 200 NSE list
    target_companies = [
        "RELIANCE",
        "TCS", "TATA",
        "HDFC", "ICICI", "SBI",
        "INFOSYS", "HCL",
        "BAJAJ", "MARUTI",
        "ASIAN PAINTS", "WIPRO",
        "LARSEN", "MAHINDRA",
        "ITC", "BHARTI",
        "KOTAK", "AXIS"
    ]

    print("="*80)
    print("TOP 200 NSE COMPANIES - ESG TESTING")
    print("Searching for major Indian companies in database")
    print("="*80)

    # Find companies in database
    found_companies = find_companies_by_name(target_companies)

    print(f"\nFound {len(found_companies)} companies from Top 200 list:")
    for i, (company_id, name) in enumerate(found_companies, 1):
        print(f"   {i:2d}. {name} (ID: {company_id})")

    if not found_companies:
        print("No companies found matching Top 200 criteria")
        return

    # Test each company
    results = []
    print(f"\n{'='*80}")
    print("TESTING ESG DATA COVERAGE")
    print(f"{'='*80}")

    for i, (company_id, company_name) in enumerate(found_companies, 1):
        print(f"\n[{i}/{len(found_companies)}] {company_name}")
        print("-" * 60)

        try:
            # Quick ESG processing test
            processor = CompanyYearProcessor(
                company_id=str(company_id),
                year=2024,
                standards=["BRSR", "CDP", "EcoVadis", "GRI"]
            )

            start_time = time.time()
            result = processor.process_company_year(
                force_refresh=True,
                include_real_time=True,
                trigger_scoring=True
            )
            processing_time = time.time() - start_time

            # Get summary
            db = get_session()
            try:
                summary = get_indicator_summary(company_id, 2024, db)
                overall = summary['overall_summary']

                indicators_count = overall['indicators_with_values']
                coverage = overall['completion_rate']

                print(f"   * Processing: {processing_time:.2f}s")
                print(f"   * Coverage: {coverage:.1f}% ({indicators_count}/151 indicators)")

                # Get sample data sources
                values = get_indicator_values(company_id, 2024, db, include_empty=False, standard="ALL")
                sources = {}
                for indicator in values['indicators']:
                    source = indicator.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1

                print(f"   * Sources: ", end="")
                source_summary = []
                for source, count in sources.items():
                    source_summary.append(f"{source}({count})")
                print(", ".join(source_summary) if source_summary else "none")

                # ESG Score
                if result.final_score:
                    print(f"   * ESG Score: {result.final_score:.1f}")

                results.append({
                    'name': company_name,
                    'id': company_id,
                    'indicators': indicators_count,
                    'coverage': coverage,
                    'processing_time': processing_time,
                    'esg_score': result.final_score,
                    'sources': sources
                })

            finally:
                db.close()

        except Exception as e:
            print(f"   X Error: {str(e)[:50]}...")
            continue

    # Results summary
    print(f"\n{'='*80}")
    print("TOP 200 COMPANIES - ESG COVERAGE SUMMARY")
    print(f"{'='*80}")

    if results:
        # Sort by indicator count
        results.sort(key=lambda x: x['indicators'], reverse=True)

        print(f"\n{'Rank':<4} {'Company':<30} {'Indicators':<12} {'Coverage':<10} {'ESG Score':<10}")
        print("-" * 70)

        for i, result in enumerate(results, 1):
            name = result['name'][:29]
            indicators = f"{result['indicators']}/151"
            coverage = f"{result['coverage']:.1f}%"
            score = f"{result['esg_score']:.1f}" if result['esg_score'] else "N/A"

            print(f"{i:<4} {name:<30} {indicators:<12} {coverage:<10} {score:<10}")

        # Top performers analysis
        print(f"\nTOP PERFORMERS:")

        excellent = [r for r in results if r['indicators'] >= 50]
        good = [r for r in results if 20 <= r['indicators'] < 50]
        basic = [r for r in results if 5 <= r['indicators'] < 20]
        limited = [r for r in results if r['indicators'] < 5]

        print(f"   Excellent (50+ indicators): {len(excellent)} companies")
        for result in excellent:
            print(f"       - {result['name']} - {result['indicators']} indicators ({result['coverage']:.1f}%)")

        print(f"   Good (20-49 indicators): {len(good)} companies")
        for result in good[:3]:  # Top 3
            print(f"       - {result['name']} - {result['indicators']} indicators ({result['coverage']:.1f}%)")

        print(f"   Basic (5-19 indicators): {len(basic)} companies")
        print(f"   Limited (1-4 indicators): {len(limited)} companies")

        # Best company details
        if results:
            best = results[0]
            print(f"\nBEST PERFORMER DETAILS:")
            print(f"   Company: {best['name']} (ID: {best['id']})")
            print(f"   Coverage: {best['coverage']:.1f}% ({best['indicators']}/151 indicators)")
            print(f"   ESG Score: {best['esg_score']:.1f}" if best['esg_score'] else "   ESG Score: Not calculated")
            print(f"   Processing Time: {best['processing_time']:.2f}s")

            if best['sources']:
                print(f"   Data Sources:")
                for source, count in best['sources'].items():
                    print(f"     * {source}: {count} indicators")

            print(f"\nRECOMMENDation:")
            print(f"   Use '{best['name']}' in your frontend for rich ESG data!")
            print(f"   Company ID: {best['id']} | Year: 2024")

    else:
        print("No successful results found")

    return results

def test_specific_company(company_name):
    """Test a specific company by name"""
    db = get_session()
    try:
        company = db.query(Company).filter(
            Company.name.ilike(f"%{company_name}%")
        ).first()

        if not company:
            print(f"Company '{company_name}' not found in database")
            return

        print(f"Testing: {company.name} (ID: {company.id})")
        # Use the existing test function
        test_top_200_companies()

    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Top 200 NSE companies ESG processing")
    parser.add_argument("--company", type=str, help="Test specific company by name")
    parser.add_argument("--list", action="store_true", help="Just list available companies")

    args = parser.parse_args()

    if args.list:
        # Just show available companies
        db = get_session()
        companies = db.query(Company).limit(20).all()
        db.close()

        print("Available companies in database:")
        for i, company in enumerate(companies, 1):
            print(f"   {i:2d}. {company.name} (ID: {company.id})")

    elif args.company:
        test_specific_company(args.company)
    else:
        # Run full Top 200 test
        results = test_top_200_companies()