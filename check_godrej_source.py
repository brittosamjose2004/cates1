#!/usr/bin/env python3
"""Check what SOURCE is shown for Godrej 2024"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')
from backend.database.db import get_session
from backend.database.models import Answer

db = get_session()

# Check Godrej 2024 - what sources are stored?
godrej_answers = db.query(Answer).filter(
    Answer.company_id == 45,
    Answer.year == 2024
).all()

print("=" * 100)
print("GODREJ INDUSTRIES LIMITED 2024 - SOURCE ATTRIBUTION IN DATABASE")
print("=" * 100)

sources_count = {}
for ans in godrej_answers:
    if ans.source not in sources_count:
        sources_count[ans.source] = 0
    sources_count[ans.source] += 1

print("\nSOURCES used:")
for source, count in sorted(sources_count.items()):
    print(f"  {source}: {count} indicators")

print("\nFirst 10 indicators with sources and values:")
for i, ans in enumerate(godrej_answers[:10]):
    if ans.answer_value:
        print(f"\n{i+1}. {ans.indicator_id}:")
        print(f"   Source: {ans.source}")
        print(f"   Confidence: {ans.confidence}")
        print(f"   Value: {str(ans.answer_value)[:70]}...")
        if ans.notes:
            print(f"   Notes: {ans.notes[:70]}...")

print("\n\n" + "=" * 100)
print("What frontend will display:")
print("=" * 100)
print("The SOURCE badges shown in frontend should show: 'real_pdf_extraction' or document path")
print("NOT 'complete_151_real_data_*' or 'manual' (those are contaminated)")

db.close()
