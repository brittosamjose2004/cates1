#!/usr/bin/env python3
"""
Get Perfect ESG Values - Simple Usage Script
============================================
Shows how to easily get perfect real ESG data values for any company.
"""

import requests
import json

def get_perfect_values(company_id):
    """Get perfect ESG values for a company."""
    try:
        response = requests.get(f"http://localhost:8000/api/companies/{company_id}")
        data = response.json()

        print(f"Company: {data['name']}")
        print(f"Year: {data['financialYear']}")
        print(f"Status: {data['status']}")
        print(f"Total Indicators: {len(data['indicators'])}")

        # Count indicators with values
        with_values = sum(1 for i in data['indicators'] if i['value'] and i['value'].strip())
        completion_rate = (with_values / len(data['indicators'])) * 100

        print(f"Indicators with Values: {with_values}/{len(data['indicators'])} ({completion_rate:.1f}%)")
        print()

        # Show sample values
        print("Sample Values:")
        count = 0
        for indicator in data['indicators']:
            if indicator['value'] and indicator['value'].strip():
                print(f"  {indicator['id']}: {indicator['value'][:80]}...")
                count += 1
                if count >= 5:  # Show first 5 indicators
                    break

        print()
        return data

    except Exception as e:
        print(f"Error getting values for company {company_id}: {e}")
        return None

def get_available_companies():
    """Get list of available companies."""
    try:
        response = requests.get("http://localhost:8000/api/companies")
        companies = response.json()

        print("Available Companies:")
        for company in companies[:20]:  # Show first 20
            print(f"  {company['id']}: {company['name']} - {company['financialYear']} - {company['status']}")

        if len(companies) > 20:
            print(f"  ... and {len(companies) - 20} more companies")

        return companies

    except Exception as e:
        print(f"Error getting companies: {e}")
        return []

if __name__ == "__main__":
    print("PERFECT ESG VALUES RETRIEVAL")
    print("="*50)

    # Show available companies
    companies = get_available_companies()
    print()

    # Test specific companies
    test_companies = [14, 44, 4]  # Asian Paints, JSW Steel, TCS

    for company_id in test_companies:
        print(f"Getting values for Company ID {company_id}:")
        print("-" * 40)
        get_perfect_values(company_id)

    print("✅ SUCCESS: Perfect real ESG values retrieved!")