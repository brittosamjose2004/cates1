#!/usr/bin/env python3
"""Check source attribution for cross-year contaminated data"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')
from backend.database.db import get_session
from backend.database.models import Answer

db = get_session()

# Check the problematic cases
contaminated_cases = [
    ('HCL Technologies Ltd', 2025, 2026),
    ('Nestle India Ltd', 2025, 2026),
    ('EMAMI LIMITED', 2025, 2026),
    ('JSW Steel Limited', 2023, 2024),
    ('TATA STEEL LIMITED', 2024, 2025),
]

print("=" * 100)
print("SOURCE ATTRIBUTION ANALYSIS - CONTAMINATED CROSS-YEAR CASES")
print("=" * 100)

for company_name, year1, year2 in contaminated_cases:
    # Query to get company id
    from backend.database.models import Company
    company = db.query(Company).filter(Company.name == company_name).first()
    
    if not company:
        print(f"\n❌ {company_name} not found")
        continue
    
    answers_y1 = db.query(Answer).filter(
        Answer.company_id == company.id,
        Answer.year == year1
    ).all()
    
    answers_y2 = db.query(Answer).filter(
        Answer.company_id == company.id,
        Answer.year == year2
    ).all()
    
    dict_y1 = {a.indicator_id: (a.answer_value, a.source) for a in answers_y1 if a.answer_value}
    dict_y2 = {a.indicator_id: (a.answer_value, a.source) for a in answers_y2 if a.answer_value}
    
    common = set(dict_y1.keys()) & set(dict_y2.keys())
    identical = [k for k in common if dict_y1[k][0] == dict_y2[k][0]]
    
    if not identical:
        continue
    
    print(f"\n{company_name} ({year1} vs {year2}):")
    print(f"  Total identical: {len(identical)}")
    
    # Show first 3 identical examples with sources
    for i, indicator_id in enumerate(sorted(identical)[:3]):
        val1, src1 = dict_y1[indicator_id]
        val2, src2 = dict_y2[indicator_id]
        print(f"\n  {indicator_id}:")
        print(f"    {year1}: source='{src1}', value={str(val1)[:60]}")
        print(f"    {year2}: source='{src2}', value={str(val2)[:60]}")
        print(f"    Same source? {src1 == src2}")
    
    # Summary of sources used
    sources_y1 = set(a.source for a in answers_y1)
    sources_y2 = set(a.source for a in answers_y2)
    print(f"\n  Sources in {year1}: {sources_y1}")
    print(f"  Sources in {year2}: {sources_y2}")

db.close()
