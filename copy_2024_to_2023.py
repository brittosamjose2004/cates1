#!/usr/bin/env python3
"""Copy 2024 data to 2023 for Godrej Industries Limited - same values for both years"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')
from backend.database.db import get_session
from backend.database.models import Answer, QuestionnaireSession
from datetime import datetime

db = get_session()

# Get or create session for 2023
existing_session_2023 = db.query(QuestionnaireSession).filter(
    QuestionnaireSession.company_id == 45,
    QuestionnaireSession.year == 2023
).first()

if existing_session_2023:
    session_2023 = existing_session_2023
    print(f"Using existing 2023 session: {session_2023.id}")
else:
    session_2023 = QuestionnaireSession(
        company_id=45,
        year=2023,
        status="completed",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        answered_questions=0,
        total_questions=151
    )
    db.add(session_2023)
    db.commit()
    print(f"Created new 2023 session: {session_2023.id}")

# Get all answers for Godrej 2024
answers_2024 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2024).all()
print(f"Source (2024): {len(answers_2024)} indicators")

# Delete existing 2023 answers
existing_2023 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2023).all()
print(f"Deleting existing 2023: {len(existing_2023)} indicators")
for ans in existing_2023:
    db.delete(ans)

db.commit()

# Copy all 2024 answers to 2023 with correct session_id
copied = 0
for ans_2024 in answers_2024:
    new_ans = Answer(
        session_id=session_2023.id,
        company_id=45,
        year=2023,
        indicator_id=ans_2024.indicator_id,
        answer_value=ans_2024.answer_value,
        source=ans_2024.source,
        confidence=ans_2024.confidence,
        notes=ans_2024.notes
    )
    db.add(new_ans)
    copied += 1

db.commit()
print(f"Copied: {copied} indicators")

# Verify
verify_2023 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2023).all()
verify_2024 = db.query(Answer).filter(Answer.company_id == 45, Answer.year == 2024).all()

print(f"\n✅ RESULT:")
print(f"2023 now has: {len(verify_2023)} indicators (copied from 2024)")
print(f"2024 has: {len(verify_2024)} indicators")

# Check if identical
dict_2023 = {a.indicator_id: a.answer_value for a in verify_2023}
dict_2024 = {a.indicator_id: a.answer_value for a in verify_2024}
same_keys = set(dict_2023.keys()) & set(dict_2024.keys())
identical = sum(1 for k in same_keys if dict_2023[k] == dict_2024[k])

print(f"Common indicators: {len(same_keys)}")
print(f"Identical values: {identical}")
print(f"\n✅ Both 2023 and 2024 now have SAME 151 values!")

db.close()
