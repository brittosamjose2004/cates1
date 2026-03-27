#!/usr/bin/env python3
"""Test that new latitude/longitude indicators are returned by API"""

import requests

# Get Godrej Industries Limited (ID 45) for 2024
print("Testing latitude/longitude indicators in API response...\n")

resp = requests.get('http://localhost:8000/api/companies/45?year=2024')

if resp.status_code == 200:
    data = resp.json()
    indicators = data.get('indicators', [])
    
    # Find the new location indicators
    lat_indicator = None
    lon_indicator = None
    
    for ind in indicators:
        if ind['id'] == 'IMP-M22-I01':
            lat_indicator = ind
        elif ind['id'] == 'IMP-M22-I02':
            lon_indicator = ind
    
    print(f"Company: {data['name']} (FY{data['dataQuality']['year_used']})")
    print(f"Total indicators returned: {len(indicators)}")
    print()
    
    if lat_indicator:
        print("✓ Latitude Indicator Found:")
        print(f"   ID: {lat_indicator['id']}")
        print(f"   Name: {lat_indicator['name']}")
        print(f"   Value: {lat_indicator.get('value')} {lat_indicator.get('unit')}")
        print(f"   Source: {lat_indicator.get('source')}")
        print()
    else:
        print("✗ Latitude indicator NOT found")
    
    if lon_indicator:
        print("✓ Longitude Indicator Found:")
        print(f"   ID: {lon_indicator['id']}")
        print(f"   Name: {lon_indicator['name']}")
        print(f"   Value: {lon_indicator.get('value')} {lon_indicator.get('unit')}")
        print(f"   Source: {lon_indicator.get('source')}")
        print()
    else:
        print("✗ Longitude indicator NOT found")
    
    if lat_indicator and lon_indicator:
        print(f"✅ SUCCESS: Both new location indicators are retrievable!")
        print(f"\nCompany Location: ({lat_indicator['value']}, {lon_indicator['value']})")
    else:
        print("\n❌ One or both indicators missing from API response")
else:
    print(f"API Error: {resp.status_code}")
    print(resp.text)
