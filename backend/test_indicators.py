"""
Test script to retrieve all 151 ESG indicator values for a company
"""
import requests
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import get_session
from backend.database.models import Company

# Test the new indicators API
def test_indicator_values(company_id=14, year=2024):
    """Test getting indicator values for a company"""

    # First, check what companies we have
    db = get_session()
    try:
        companies = db.query(Company).limit(5).all()
        print("Available companies:")
        for comp in companies:
            print(f"  {comp.id}: {comp.name}")

        # Get specific company
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found!")
            return

        print(f"\nTesting indicator values for: {company.name} (ID: {company_id}), Year: {year}")
        print("=" * 80)

    finally:
        db.close()

    # Test the API endpoints via direct import (since we may not have server running)
    try:
        from backend.api.routers.indicators import get_indicator_summary, get_indicator_values
        from backend.database.db import get_session

        db = get_session()

        # 1. Get summary
        print("\n1. SUMMARY:")
        summary = get_indicator_summary(company_id, year, db)
        print(f"   Overall completion: {summary['overall_summary']['completion_rate']}%")
        print(f"   Indicators with values: {summary['overall_summary']['indicators_with_values']}/151")

        print(f"\n   Top 10 modules by completion:")
        for module in summary['module_breakdown'][:10]:
            print(f"     {module['module_name'][:40]:40}: {module['completion_rate']:5.1f}% ({module['indicators_with_values']}/{module['total_indicators']})")

        # 2. Get actual values (only with data)
        print(f"\n2. INDICATOR VALUES (showing only indicators with data):")
        values = get_indicator_values(company_id, year, db, include_empty=False)

        print(f"   Found {len(values['indicators'])} indicators with actual values:")

        for i, indicator in enumerate(values['indicators'][:20], 1):  # Show first 20
            print(f"   {i:2d}. {indicator['indicator_id']:12} | {indicator['source']:10} | {str(indicator['answer_value'])[:50]}")
            print(f"       {indicator['indicator_name'][:70]}")
            if indicator['notes']:
                print(f"       Notes: {indicator['notes'][:60]}")
            print()

        if len(values['indicators']) > 20:
            print(f"       ... and {len(values['indicators']) - 20} more indicators with values")

        print(f"\n3. STANDARD BREAKDOWN:")
        for standard in ["BRSR", "CDP", "EcoVadis", "GRI"]:
            std_values = get_indicator_values(company_id, year, db, include_empty=False, standard=standard)
            print(f"   {standard:8}: {len(std_values['indicators'])} indicators with values")

        db.close()

    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # You can change these values
    company_id = 14  # Asian Paints
    year = 2024

    test_indicator_values(company_id, year)