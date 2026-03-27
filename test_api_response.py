#!/usr/bin/env python3
"""Test actual API endpoint response"""

import requests

# Correct endpoint: /api/companies/45?year=2024
resp = requests.get('http://localhost:8000/api/companies/45?year=2024')
if resp.status_code == 200:
    data = resp.json()
    print("✅ API Response successful (Status 200)")
    print(f"\nCompany: {data.get('name')}")
    print(f"Year: {data.get('dataQuality', {}).get('year_used')}")
    
    indicators = data.get('indicators', [])
    print(f"\nTotal indicators: {len(indicators)}")
    
    # Check first 3 indicators with source_details
    print("\nFirst 3 indicators with SOURCE details:")
    for i, ind in enumerate(indicators[:3]):
        print(f"\n{i+1}. ID: {ind.get('id')} - {ind.get('name')[:60]}")
        print(f"   Source: {ind.get('source')}")
        if ind.get('source_details'):
            details = ind['source_details']
            location = details.get('location', 'N/A')
            resource = details.get('resource', 'N/A')
            print(f"   Resource: {resource}")
            print(f"   Location: {location}")
            
            if 'Godrej' in location:
                print("   ✅ Shows Godrej path (CORRECT!)")
            elif 'Infosys' in location:
                print("   ❌ Still shows Infosys path (BUG!)")
        else:
            print("   ⚠️  No source_details")
else:
    print(f'❌ API Error: {resp.status_code}')
    print(resp.text)
