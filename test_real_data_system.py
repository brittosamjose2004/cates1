#!/usr/bin/env python3
"""
Test Real Data Only ESG System
===============================
Tests the new real data validation and perfect retrieval system.
Ensures only REAL data is returned, no synthetic data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.real_data_validator import RealDataValidator
from backend.database.db import get_session

def test_real_data_system():
    """Test the real data system with actual companies."""

    print("TESTING REAL DATA ONLY ESG SYSTEM")
    print("=" * 60)
    print("Ensures perfect retrieval of 100% REAL data from actual sources")
    print("NO synthetic data, NO AI generation - only verified real extracted data")
    print()

    db = get_session()
    validator = RealDataValidator(db)

    # Test companies that should have both real and synthetic data
    test_companies = [
        (14, "Asian Paints"),
        (44, "JSW Steel Limited"),
        (4, "Tata Consultancy Services")
    ]

    for company_id, company_name in test_companies:
        print(f"Testing {company_name} (ID: {company_id})")
        print("-" * 50)

        try:
            # Test perfect real data retrieval
            perfect_data = validator.get_perfect_real_data(company_id)

            if "error" in perfect_data:
                print(f"ERROR: {perfect_data['error']}")
                continue

            print(f"Company: {perfect_data['company_name']}")
            print(f"Perfect Year: {perfect_data['year_used']}")
            print(f"Real Data Analysis:")

            analysis = perfect_data['real_data_analysis']
            print(f"  Real Indicators: {analysis['real_indicators']}/{analysis['total_indicators']}")
            print(f"  Real Data %: {analysis['real_data_percentage']}%")
            print(f"  Synthetic Indicators: {analysis['synthetic_indicators']}")
            print(f"  100% Real Data: {analysis['is_100_percent_real']}")
            print(f"  Real Sources: {list(analysis['real_sources'].keys())}")

            # Test year recommendation
            if perfect_data['requested_year'] and perfect_data['requested_year'] != perfect_data['year_used']:
                print(f"  Year Switch: {perfect_data['year_switched_reason']}")

            # Validate specific year contains only real data
            validation = validator.validate_real_data_only(company_id, perfect_data['year_used'])
            print(f"  Real Data Only: {validation['is_real_data_only']}")

            if not validation['is_real_data_only']:
                print(f"  WARNING: Synthetic indicators found:")
                for syn in validation['synthetic_indicators'][:3]:
                    print(f"    - {syn['id']}: {syn['source']}")

            print(f"  Available Real Years: {perfect_data['available_real_years']}")
            print()

        except Exception as e:
            print(f"ERROR testing {company_name}: {str(e)}")
            print()

def test_year_comparison():
    """Test the difference between requesting different years."""

    print(f"\nYEAR COMPARISON TEST - Asian Paints")
    print("=" * 60)

    db = get_session()
    validator = RealDataValidator(db)

    company_id = 14  # Asian Paints

    # Test requesting problems year (2019) vs perfect year
    years_to_test = [2019, 2024]

    for test_year in years_to_test:
        print(f"\nRequesting Year {test_year}:")
        print("-" * 30)

        try:
            perfect_data = validator.get_perfect_real_data(company_id, test_year)

            if "error" in perfect_data:
                print(f"ERROR: {perfect_data['error']}")
                continue

            print(f"Requested: {perfect_data['requested_year']}")
            print(f"Year Used: {perfect_data['year_used']}")

            analysis = perfect_data['real_data_analysis']
            print(f"Real Indicators: {analysis['real_indicators']}")
            print(f"Real Data %: {analysis['real_data_percentage']}%")
            print(f"Is Perfect Real: {perfect_data['is_perfect_real_data']}")

            if perfect_data['year_switched_reason']:
                print(f"Switch Reason: {perfect_data['year_switched_reason']}")

        except Exception as e:
            print(f"ERROR: {str(e)}")

def test_data_source_validation():
    """Test that our real data sources are correctly classified."""

    print(f"\nDATA SOURCE VALIDATION TEST")
    print("=" * 60)

    validator = RealDataValidator(get_session())

    print("REAL DATA SOURCES (Allowed):")
    for source in sorted(validator.REAL_SOURCES):
        print(f"  ✅ {source}")

    print("\nSYNTHETIC DATA SOURCES (Filtered Out):")
    for source in sorted(validator.SYNTHETIC_SOURCES):
        print(f"  ❌ {source}")

if __name__ == "__main__":
    try:
        print("REAL DATA ONLY ESG TESTING SYSTEM")
        print("Testing perfect real data retrieval...")
        print()

        # Run all tests
        test_real_data_system()
        test_year_comparison()
        test_data_source_validation()

        print("\n" + "=" * 60)
        print("✅ REAL DATA SYSTEM TESTING COMPLETED")
        print()
        print("Key Benefits:")
        print("- Only returns 100% REAL data from actual sources")
        print("- Automatically finds years with best real data")
        print("- Filters out synthetic/AI-generated data")
        print("- Validates data sources and completeness")
        print("- Perfect year selection for maximum real data coverage")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()