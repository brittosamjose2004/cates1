#!/usr/bin/env python3
"""Check if Godrej Industries Limited has identical values between 2023 and 2024"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')
from backend.database.db import get_session
from backend.database.models import Answer

db = get_session()

# Get all answers for Godrej 2023 and 2024
answers_2023 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2023).all()
answers_2024 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2024).all()

print(f"Total indicators 2023: {len(answers_2023)}")
print(f"Total indicators 2024: {len(answers_2024)}")

# Build dictionaries by indicator_id
dict_2023 = {a.indicator_id: a.answer_value for a in answers_2023 if a.answer_value}
dict_2024 = {a.indicator_id: a.answer_value for a in answers_2024 if a.answer_value}

print(f"\nFilled indicators 2023: {len(dict_2023)}")
print(f"Filled indicators 2024: {len(dict_2024)}")

# Check for identical values
identical_count = 0
different_count = 0
same_keys = set(dict_2023.keys()) & set(dict_2024.keys())

for key in same_keys:
    if dict_2023[key] == dict_2024[key]:
        identical_count += 1
    else:
        different_count += 1

print(f"\nComparison for {len(same_keys)} common indicators:")
print(f"  Identical values: {identical_count}")
print(f"  Different values: {different_count}")

# Show first 5 examples of identical values
print(f"\nFirst 5 IDENTICAL (potential cross-year copy):")
count = 0
for key in sorted(same_keys):
    if dict_2023[key] == dict_2024[key]:
        value_preview = str(dict_2023[key])[:80]
        print(f"  {key}: {value_preview}")
        count += 1
        if count >= 5:
            break

# Show first 5 examples of different values
print(f"\nFirst 5 DIFFERENT (good sign - year-specific):")
count = 0
for key in sorted(same_keys):
    if dict_2023[key] != dict_2024[key]:
        val23 = str(dict_2023[key])[:60]
        val24 = str(dict_2024[key])[:60]
        print(f"  {key}:")
        print(f"    2023: {val23}")
        print(f"    2024: {val24}")
        count += 1
        if count >= 5:
            break

db.close()
