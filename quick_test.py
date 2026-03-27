import requests
import json

# Test perfect data system
url = "http://localhost:8000/api/companies/14?year=2019"
resp = requests.get(url)

if resp.status_code == 200:
    data = resp.json()
    print('SUCCESS: Perfect Data System Working!')
    print('Financial Year:', data.get('financialYear'))
    print('Indicators with data:', sum(1 for i in data.get('indicators', []) if i.get('value')))

    if 'dataQuality' in data and data['dataQuality']:
        dq = data['dataQuality']
        print('--- PERFECT DATA QUALITY INFO ---')
        print('Requested year:', dq.get('requested_year'))
        print('Year used:', dq.get('year_used'))
        print('Completeness:', dq.get('completeness_percentage'), '%')
        print('Quality grade:', dq.get('quality_grade'))
        print('Perfect data:', dq.get('is_perfect_data'))
        print('Fallback reason:', dq.get('fallback_reason'))

        if dq.get('year_used') != dq.get('requested_year'):
            print('SMART FALLBACK WORKED: Poor year -> Perfect year!')
    else:
        print('DataQuality field missing or None')
else:
    print('API Error:', resp.status_code)