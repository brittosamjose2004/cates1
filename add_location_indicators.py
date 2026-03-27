#!/usr/bin/env python3
"""Add latitude and longitude indicators to the questionnaire CSV"""

import csv
from pathlib import Path

# CSV file path
csv_file = Path("Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv")

# New indicators to add
new_indicators = [
    [
        "IMP-M22-I01",
        "Location Information",
        "Headquarters Latitude",
        'What is the latitude coordinate of your company headquarters location?',
        "Numeric",
        "Decimal degrees (-90 to +90)",
        "As at reporting date",
        "Provide the latitude coordinate of the registered headquarters or principal place of business in decimal degrees format (e.g., 19.0825). This enables geographic mapping of ESG performance across regions.",
        "—",
        "—",
        "—",
        "—",
        "0",
        "",
        "",
        "",
        ""
    ],
    [
        "IMP-M22-I02",
        "Location Information",
        "Headquarters Longitude",
        'What is the longitude coordinate of your company headquarters location?',
        "Numeric",
        "Decimal degrees (-180 to +180)",
        "As at reporting date",
        "Provide the longitude coordinate of the registered headquarters or principal place of business in decimal degrees format (e.g., 72.8563). Combined with latitude, this enables geographic mapping of ESG initiatives.",
        "—",
        "—",
        "—",
        "—",
        "0",
        "",
        "",
        "",
        ""
    ]
]

# Read existing CSV
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Append new indicators
for indicator in new_indicators:
    rows.append(indicator)

# Write back
with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print(f"✓ Added 2 new indicators:")
print(f"  - IMP-M22-I01: Headquarters Latitude")
print(f"  - IMP-M22-I02: Headquarters Longitude")
print(f"\nTotal lines in CSV: {len(rows)}")
