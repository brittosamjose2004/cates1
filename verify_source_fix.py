#!/usr/bin/env python3
"""Quick verification of SOURCE fix for Godrej"""

import requests
import json

# Test the exact case from the conversation - Godrej Industries Limited 2024
print("="*60)
print("VERIFICATION: Source Path Fix for Godrej Industries Limited")
print("="*60)

resp = requests.get('http://localhost:8000/api/companies/45?year=2024')
if resp.status_code == 200:
    data = resp.json()
    
    print(f"\nCompany: {data['name']}")
    print(f"Year: {data['dataQuality']['year_used']}")
    print(f"Indicators with data: {data['dataQuality']['indicators_with_data']} / {data['dataQuality']['total_indicators']}")
    
    # Show first indicator source path
    if data['indicators']:
        ind = data['indicators'][0]
        print(f"\nFirst indicated source path:")
        print(f"  Indicator ID: {ind['id']}")
        print(f"  Source Code: {ind['source']}")
        
        if ind.get('source_details'):
            details = ind['source_details']
            print(f"  Resource: {details['resource']}")
            print(f"  Location: {details['location']}")
            
            # Verify it's the company's own PDF
            if 'Godrej' in details['location']:
                print(f"\n[SUCCESS] SOURCE now shows Godrej's own PDF path!")
                print(f"       (Not hardcoded Infosys path as before)")
            else:
                print(f"\n[WARNING] Location doesn't contain 'Godrej'")
else:
    print(f"API Error: {resp.status_code}")
    print(resp.text)
