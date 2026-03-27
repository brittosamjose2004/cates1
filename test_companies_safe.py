#!/usr/bin/env python3
"""
Unicode-safe CLI test for real companies
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company
from backend.services.company_year_processor import CompanyYearProcessor
from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
import time

def safe_print(text):
    """Print text safely, removing problematic Unicode characters"""
    # Replace common problematic characters
    text = str(text).replace('₹', 'INR ').replace('—', '-').replace('•', '-')
    try:
        print(text)
    except UnicodeEncodeError:
        # If still failing, encode to ASCII
        print(text.encode('ascii', 'ignore').decode('ascii'))

def test_company_simple(company_id, company_name, year=2024):
    """Simple test for a specific company"""
    safe_print(f"================================================================================")
    safe_print(f"ESG PROCESSING TEST: {company_name}")
    safe_print(f"Company ID: {company_id} | Year: {year}")
    safe_print(f"================================================================================")

    try:
        # 1. Run ESG Pipeline
        safe_print(f"\n1. RUNNING ESG PIPELINE...")

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

        safe_print(f"   RESULTS:")
        safe_print(f"   - Total Indicators: {result.total_indicators}")
        safe_print(f"   - Processed: {result.processed_indicators}")
        safe_print(f"   - Failed: {result.failed_indicators}")
        safe_print(f"   - Processing Time: {result.processing_time_seconds:.2f}s")
        if result.final_score:
            safe_print(f"   - ESG Score: {result.final_score:.1f}")

        # 2. Get Summary
        safe_print(f"\n2. DATA SUMMARY:")
        db = get_session()
        try:
            summary = get_indicator_summary(company_id, year, db)
            overall = summary['overall_summary']

            safe_print(f"   - Coverage: {overall['completion_rate']:.1f}% ({overall['indicators_with_values']}/151)")

            # Count by source
            values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

            sources = {}
            for indicator in values['indicators']:
                source = indicator.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

            safe_print(f"   - Data Sources:")
            for source, count in sources.items():
                safe_print(f"     {source}: {count} indicators")

        finally:
            db.close()

        # 3. Standards Coverage
        safe_print(f"\n3. STANDARDS:")
        db = get_session()
        try:
            for standard in ["BRSR", "CDP", "EcoVadis", "GRI"]:
                std_values = get_indicator_values(company_id, year, db, include_empty=False, standard=standard)
                safe_print(f"   - {standard}: {len(std_values['indicators'])} indicators")
        finally:
            db.close()

        # 4. Sample Values (Unicode-safe)
        safe_print(f"\n4. SAMPLE VALUES:")
        db = get_session()
        try:
            values = get_indicator_values(company_id, year, db, include_empty=False, standard="ALL")

            if values['indicators']:
                safe_print(f"   Found {len(values['indicators'])} indicators with data:")
                for i, indicator in enumerate(values['indicators'][:5], 1):
                    indicator_id = indicator.get('indicator_id', 'N/A')
                    source = indicator.get('source', 'unknown')
                    answer_value = str(indicator.get('answer_value', 'N/A'))

                    # Clean the value for safe display
                    clean_value = answer_value.replace('₹', 'INR ').replace('—', '-')
                    if len(clean_value) > 40:
                        clean_value = clean_value[:40] + "..."

                    safe_print(f"   {i}. {indicator_id} | {source} | {clean_value}")
            else:
                safe_print(f"   No indicators found with values")

        finally:
            db.close()

        return overall['indicators_with_values'], overall['completion_rate']

    except Exception as e:
        safe_print(f"ERROR: {e}")
        return 0, 0.0

if __name__ == "__main__":
    # Get available companies
    db = get_session()
    companies = db.query(Company).limit(10).all()
    db.close()

    safe_print("Available companies for testing:")
    for i, company in enumerate(companies, 1):
        safe_print(f"   {i}. {company.name} (ID: {company.id})")

    safe_print(f"\n" + "="*80)
    safe_print("TESTING TOP 5 COMPANIES")
    safe_print("="*80)

    results = []

    # Test top 5 companies
    for i, company in enumerate(companies[:5], 1):
        safe_print(f"\n[{i}/5] Testing: {company.name}")
        indicators_count, coverage = test_company_simple(company.id, company.name)
        results.append({
            'name': company.name,
            'indicators': indicators_count,
            'coverage': coverage
        })

    # Summary
    safe_print(f"\n" + "="*80)
    safe_print("SUMMARY RESULTS")
    safe_print("="*80)

    results.sort(key=lambda x: x['indicators'], reverse=True)

    safe_print(f"{'Company':<35} {'Indicators':<12} {'Coverage'}")
    safe_print("-" * 60)

    for result in results:
        name = result['name'][:34]
        indicators = f"{result['indicators']}/151"
        coverage = f"{result['coverage']:.1f}%"
        safe_print(f"{name:<35} {indicators:<12} {coverage}")

    # Best performer
    if results:
        best = results[0]
        safe_print(f"\nBEST PERFORMER:")
        safe_print(f"   Company: {best['name']}")
        safe_print(f"   Indicators: {best['indicators']}/151 ({best['coverage']:.1f}%)")

        if best['indicators'] > 100:
            safe_print(f"   STATUS: EXCELLENT - High ESG data coverage!")
        elif best['indicators'] > 50:
            safe_print(f"   STATUS: GOOD - Moderate ESG data coverage")
        else:
            safe_print(f"   STATUS: BASIC - Limited ESG data available")