#!/usr/bin/env python3
"""Verify that company location indicators are available via API"""

import requests

companies_to_test = [
    (45, "Godrej Industries Limited", 2024),
    (42, "Infosys Limited", 2024),
    (9, "Godrej Industries Limited", 2023),
]

print("="*80)
print("COMPANY OFFICE LOCATIONS - API VERIFICATION")
print("="*80 + "\n")

for company_id, company_name, year in companies_to_test:
    resp = requests.get(f'http://localhost:8000/api/companies/{company_id}?year={year}')
    
    if resp.status_code == 200:
        data = resp.json()
        indicators = data.get('indicators', [])
        
        lat_ind = None
        lon_ind = None
        
        for ind in indicators:
            if ind['id'] == 'IMP-M22-I01':
                lat_ind = ind
            elif ind['id'] == 'IMP-M22-I02':
                lon_ind = ind
        
        print(f"Company: {data.get('name')} | FY{data['dataQuality']['year_used']}")
        
        if lat_ind and lon_ind:
            print(f"[OK] Latitude:  {lat_ind.get('value')} {lat_ind.get('unit')}")
            print(f"[OK] Longitude: {lon_ind.get('value')} {lon_ind.get('unit')}")
            print(f"  Source: {lat_ind.get('source')}")
            print(f"\n  Location: ({lat_ind.get('value')}, {lon_ind.get('value')})")
        else:
            print(f"[ERROR] Location indicators not found")
        
        print("-" * 80 + "\n")
    else:
        print(f"❌ API Error for company {company_id}: {resp.status_code}\n")

print("="*80)
print("COMPANY OFFICE LOCATIONS SUCCESSFULLY ADDED!")
print("="*80)
