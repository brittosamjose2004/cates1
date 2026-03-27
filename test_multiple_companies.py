#!/usr/bin/env python3
"""Test SOURCE paths for multiple companies"""

import requests

# Get list of companies
resp = requests.get('http://localhost:8000/api/companies')
if resp.status_code == 200:
    companies = resp.json()
    print(f"Testing first 3 companies for SOURCE path fix:\n")
    
    for company in companies[:3]:
        company_id = company['id']
        company_name = company['name']
        year = 2024  # Use latest year
        
        # Get company details with year
        detail_resp = requests.get(f'http://localhost:8000/api/companies/{company_id}?year={year}')
        if detail_resp.status_code == 200:
            detail = detail_resp.json()
            year_used = detail.get('dataQuality', {}).get('year_used', 'N/A')
            
            indicators = detail.get('indicators', [])
            if indicators:
                first_ind = indicators[0]
                source_details = first_ind.get('source_details', {})
                location = source_details.get('location', 'N/A')
                
                print(f"{company_id}. {company_name} (FY{year_used})")
                print(f"   Location: {location}")
                
                if company_name.lower() in location.lower():
                    print(f"   [OK] Shows {company_name} path (CORRECT)")
                elif 'Infosys' in location:
                    print(f"   [ERROR] Still shows Infosys path (BUG)")
                else:
                    print(f"   [INFO] Shows different company path")
                print()
