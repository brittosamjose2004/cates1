#!/usr/bin/env python3
"""
CLI Test Script: Real Companies ESG Processing
Tests ESG pipeline with actual companies from Top 200 list
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company
from backend.services.company_year_processor import CompanyYearProcessor
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
import time

def get_available_companies(limit=20):
    """Get list of companies from database"""
    db = get_session()
    try:
        companies = db.query(Company).limit(limit).all()
        return [(c.id, c.name) for c in companies]
    finally:
        db.close()

def test_company_esg_processing(company_id, company_name, year=2024):
    """Test ESG processing for a specific company"""
    print("="*80)
    print(f"ESG PROCESSING TEST: {company_name}")
    print(f"Company ID: {company_id} | Year: {year}")
    print("="*80)

    try:
        # 1. Run ESG Pipeline
        print(f"\n1. RUNNING ESG PIPELINE...")
        start_time = time.time()

        processor = CompanyYearProcessor(
            company_id=str(company_id),
            year=year,
            standards=["BRSR", "CDP", "EcoVadis", "GRI"]
        )

        result = processor.process_company_year(
            force_refresh=True,
            include_real_time=True,
            trigger_scoring=True
        )

        processing_time = time.time() - start_time
        print(f"   Processing completed in {processing_time:.2f}s")
        print(f"   Total Indicators: {result.total_indicators}")
        print(f"   Processed: {result.processed_indicators}")
        print(f"   Failed: {result.failed_indicators}")
        print(f"   Modules: {len(result.modules_processed)}")

        if result.final_score:
            print(f"   ESG Score: {result.final_score:.1f}")

        # 2. Get Summary via API
        print(f"\n2. INDICATOR SUMMARY:")
        db = get_session()
        try:
            summary = get_indicator_summary(company_id, year, db)
            overall = summary['overall_summary']

            print(f"   Coverage: {overall['completion_rate']:.1f}%")
            print(f"   Indicators with values: {overall['indicators_with_values']}/151")

            # Show top modules with data
            modules_with_data = [m for m in summary['module_breakdown'] if m['indicators_with_values'] > 0]
            modules_with_data.sort(key=lambda x: x['indicators_with_values'], reverse=True)

            print(f"   Top modules with data:")
            for module in modules_with_data[:5]:
                print(f"     {module['module_name'][:45]:45}: {module['indicators_with_values']:2d}/{module['total_indicators']:2d} ({module['completion_rate']:5.1f}%)")

        finally:
            db.close()

        # 3. Show Sample Values
        print(f"\n3. SAMPLE INDICATOR VALUES:")
        db = get_session()
        try:
            values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

            if values['indicators']:
                print(f"   Found {len(values['indicators'])} indicators with values:")
                for i, indicator in enumerate(values['indicators'][:10], 1):
                    indicator_id = indicator.get('indicator_id', 'N/A')
                    answer_value = indicator.get('answer_value', 'N/A')
                    source = indicator.get('source', 'unknown')
                    value_preview = str(answer_value)[:50] + "..." if len(str(answer_value)) > 50 else str(answer_value)
                    print(f"   {i:2d}. {indicator_id:12} | {source:10} | {value_preview}")
            else:
                print(f"   No indicators found with values")

        finally:
            db.close()

        # 4. Standards Breakdown
        print(f"\n4. STANDARDS COVERAGE:")
        db = get_session()
        try:
            for standard in ["BRSR", "CDP", "EcoVadis", "GRI"]:
                std_values = get_indicator_values(company_id, year, db, include_empty=False, standard=standard)
                print(f"   {standard:8}: {len(std_values['indicators']):3d} indicators")
        finally:
            db.close()

        return {
            'company_id': company_id,
            'company_name': company_name,
            'indicators_with_values': overall['indicators_with_values'],
            'completion_rate': overall['completion_rate'],
            'processing_time': processing_time,
            'esg_score': result.final_score
        }

    except Exception as e:
        print(f"ERROR processing {company_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_multi_company_test():
    """Test ESG processing across multiple real companies"""
    print("="*80)
    print("MULTI-COMPANY ESG PROCESSING TEST")
    print("Testing real companies from Top 200 list")
    print("="*80)

    # Get available companies
    companies = get_available_companies(15)
    print(f"\nFound {len(companies)} companies in database:")
    for i, (company_id, name) in enumerate(companies, 1):
        print(f"   {i:2d}. {name} (ID: {company_id})")

    # Test each company
    results = []

    for i, (company_id, company_name) in enumerate(companies[:10], 1):
        print(f"\n\n[{i}/10] Testing: {company_name}")
        result = test_company_esg_processing(company_id, company_name, year=2024)
        if result:
            results.append(result)

    # Summary Report
    print("\n")
    print("="*80)
    print("MULTI-COMPANY TEST SUMMARY")
    print("="*80)

    if results:
        results.sort(key=lambda x: x['indicators_with_values'], reverse=True)

        print(f"\n{'Rank':<4} {'Company':<35} {'Indicators':<12} {'Coverage':<10} {'Score':<8} {'Time':<8}")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            company_name = result['company_name'][:34]
            indicators = f"{result['indicators_with_values']}/151"
            coverage = f"{result['completion_rate']:.1f}%"
            score = f"{result['esg_score']:.1f}" if result['esg_score'] else "N/A"
            time = f"{result['processing_time']:.2f}s"

            print(f"{i:<4} {company_name:<35} {indicators:<12} {coverage:<10} {score:<8} {time:<8}")

        # Best performers
        best = results[0]
        print(f"\nBEST PERFORMER:")
        print(f"   Company: {best['company_name']}")
        print(f"   Coverage: {best['completion_rate']:.1f}% ({best['indicators_with_values']}/151 indicators)")
        print(f"   ESG Score: {best['esg_score']:.1f}" if best['esg_score'] else "   ESG Score: Not calculated")

    else:
        print("No successful processing results found")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test ESG processing with real companies")
    parser.add_argument("--company_id", type=int, help="Test specific company ID")
    parser.add_argument("--company_name", type=str, help="Company name (for display)")
    parser.add_argument("--year", type=int, default=2024, help="Year to process")
    parser.add_argument("--multi", action="store_true", help="Test multiple companies")

    args = parser.parse_args()

    if args.multi:
        run_multi_company_test()
    elif args.company_id:
        company_name = args.company_name or f"Company {args.company_id}"
        test_company_esg_processing(args.company_id, company_name, args.year)
    else:
        # Default: run multi-company test
        print("Running multi-company ESG processing test...")
        run_multi_company_test()