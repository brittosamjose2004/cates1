#!/usr/bin/env python3
"""Test SOURCE paths specifically for real_pdf_extraction"""

import requests

# Get list of companies
resp = requests.get('http://localhost:8000/api/companies')
if resp.status_code == 200:
    companies = resp.json()
    print(f"Searching for companies with real_pdf_extraction SOURCE...\n")
    
    found_count = 0
    for company in companies:
        if found_count >= 3:
            break
            
        company_id = company['id']
        company_name = company['name']
        
        # Try different years
        for year in [2024, 2025, 2023]:
            detail_resp = requests.get(f'http://localhost:8000/api/companies/{company_id}?year={year}')
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                year_used = detail.get('dataQuality', {}).get('year_used', 'N/A')
                
                indicators = detail.get('indicators', [])
                for ind in indicators:
                    if ind.get('source') == 'real_pdf_extraction':
                        found_count += 1
                        first_ind = ind
                        source_details = first_ind.get('source_details', {})
                        location = source_details.get('location', 'N/A')
                        
                        print(f"{found_count}. {company_name} (FY{year_used}) / Indicator {first_ind.get('id')}")
                        print(f"   Location: {location[:80]}...")
                        
                        if company_name.lower() in location.lower():
                            print(f"   [OK] Shows company name in path")
                        elif 'Infosys' in location:
                            print(f"   [ERROR] Still shows Infosys path")
                        else:
                            print(f"   [CHECK] Path doesn't obviously match company")
                        print()
                        break
                        
                if found_count >= 3:
                    break
