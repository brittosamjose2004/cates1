#!/usr/bin/env python3
"""Investigate cross-year data contamination - check all companies for year mixing"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')
from backend.database.db import get_session
from backend.database.models import Answer, Company

db = get_session()

print("=" * 80)
print("CROSS-YEAR DATA CONTAMINATION INVESTIGATION")
print("=" * 80)

# Get all companies with multiple years of data
companies = db.query(Company).all()

contamination_found = []

for company in companies:
    # Get all years for this company
    years_query = db.query(Answer.year).filter(Answer.company_id == company.id).distinct().all()
    years = sorted([y[0] for y in years_query])
    
    if len(years) < 2:
        continue
    
    # Check adjacent years for identical values
    for i in range(len(years) - 1):
        year1 = years[i]
        year2 = years[i + 1]
        
        answers_y1 = db.query(Answer).filter(
            Answer.company_id == company.id,
            Answer.year == year1
        ).all()
        
        answers_y2 = db.query(Answer).filter(
            Answer.company_id == company.id,
            Answer.year == year2
        ).all()
        
        if not answers_y1 or not answers_y2:
            continue
        
        dict_y1 = {a.indicator_id: a.answer_value for a in answers_y1 if a.answer_value}
        dict_y2 = {a.indicator_id: a.answer_value for a in answers_y2 if a.answer_value}
        
        # Find common indicators with identical values
        common = set(dict_y1.keys()) & set(dict_y2.keys())
        identical = [k for k in common if dict_y1[k] == dict_y2[k]]
        
        if identical:
            identical_pct = (len(identical) / len(common)) * 100 if common else 0
            if identical_pct > 50:  # Flag if more than 50% are identical
                contamination_found.append({
                    'company': company.name,
                    'year1': year1,
                    'year2': year2,
                    'common': len(common),
                    'identical': len(identical),
                    'identical_pct': identical_pct
                })

print(f"\n🔍 RESULTS:")
if contamination_found:
    print(f"\n⚠️ CROSS-YEAR CONTAMINATION DETECTED ({len(contamination_found)} cases):")
    for case in contamination_found:
        print(f"\n  {case['company']} ({case['year1']} vs {case['year2']}):")
        print(f"    Common indicators: {case['common']}")
        print(f"    Identical values: {case['identical']} ({case['identical_pct']:.1f}%)")
else:
    print("\n✅ NO CROSS-YEAR CONTAMINATION DETECTED")
    print("All years have distinct values (no unwanted copying)")

db.close()
