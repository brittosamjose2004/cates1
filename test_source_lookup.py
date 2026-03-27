#!/usr/bin/env python3
"""Verify SOURCE path lookup matches actual company PDFs"""

import sys
sys.path.insert(0, r'F:\impactree cates\cates-main')

from source_tracking_service import format_source_for_frontend

# Test with Godrej 2024
print("=" * 80)
print("SOURCE PATH LOOKUP TEST - Godrej 2024")
print("=" * 80)

source_details = format_source_for_frontend("real_pdf_extraction", "IMP-M01-I01", company_id=45, year=2024)

print(f"\nSource Code: {source_details['source_code']}")
print(f"Display Name: {source_details['name']}")
print(f"Resource: {source_details['resource']}")
print(f"Location: {source_details['location']}")
print(f"Reliability: {source_details['reliability']}")

if "Godrej" in source_details['location'] and "Infosys" not in source_details['location']:
    print("\n✅ SUCCESS - SOURCE shows Godrej path, not Infosys!")
elif "Infosys" in source_details['location']:
    print("\n❌ FAIL - SOURCE still shows Infosys path!")
else:
    print(f"\n⚠️ SOURCE shows: {source_details['location']}")
