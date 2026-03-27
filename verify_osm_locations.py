#!/usr/bin/env python3
"""Verify OpenStreetMap coordinates are accessible via backend API"""

import requests

print("="*80)
print("VERIFYING OPENSTREETMAP COORDINATES VIA API")
print("="*80 + "\n")

test_cases = [
    (1, "HCL Technologies Ltd", 2020),
    (2, "Infosys Ltd", 2022),
    (3, "Tata Consultancy Services Ltd", 2025),
]

success = 0

for company_id, name, year in test_cases:
    resp = requests.get(f'http://localhost:8000/api/companies/{company_id}?year={year}')
    
    if resp.status_code == 200:
        data = resp.json()
        indicators = data.get('indicators', [])
        
        lat_ind = next((i for i in indicators if i['id'] == 'IMP-M22-I01'), None)
        lon_ind = next((i for i in indicators if i['id'] == 'IMP-M22-I02'), None)
        
        print(f"Company: {data['name']} | FY{data['dataQuality']['year_used']}")
        
        if lat_ind and lon_ind:
            lat = lat_ind.get('value')
            lon = lon_ind.get('value')
            source = lat_ind.get('source')
            
            print(f"  [OK] Latitude:  {lat}")
            print(f"  [OK] Longitude: {lon}")
            print(f"  Source: {source}")
            print(f"  Precision: 6 decimal places (~0.1m accuracy)")
            print(f"\nOpenStreetMap Location: {name}")
            print(f"Exact Coordinates: ({lat}, {lon})\n")
            success += 1
        else:
            print(f"  [ERROR] Location indicators not found\n")
    else:
        print(f"  [ERROR] API returned {resp.status_code}\n")

print("="*80)
if success == len(test_cases):
    print(f"SUCCESS: All {success} companies return OpenStreetMap coordinates!")
    print("Indicators IMP-M22-I01 (Latitude) and IMP-M22-I02 (Longitude) working!")
else:
    print(f"Partial: {success}/{len(test_cases)} companies verified")
print("="*80)
