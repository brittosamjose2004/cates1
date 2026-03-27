#!/usr/bin/env python3
"""
TARGETED BRSR DATA EXTRACTOR
Extracts structured ESG data from identified BRSR section (pages 380-428)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import re
import PyPDF2
from typing import Dict
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def extract_brsr_structured_data(company_id: int, year: int = 2024):
    """Extract from the identified BRSR section with targeted patterns"""

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print("="*70)
        print(f"TARGETED BRSR EXTRACTION - {company.name}")
        print("="*70)

        # Get PDF
        pdf_file = Path('data/annual_reports/ITC_LIMITED/ITC_FY2025_annual.pdf')

        with open(pdf_file, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)

            # Extract BRSR pages (380-428, about 48 pages)
            brsr_text = ''
            brsr_start = 380  # Page 381 in 1-based indexing
            brsr_end = min(428, len(pdf.pages))

            print(f"Extracting BRSR pages {brsr_start + 1} to {brsr_end}...")

            for page_num in range(brsr_start, brsr_end):
                brsr_text += pdf.pages[page_num].extract_text()

            print(f"Extracted {len(brsr_text):,} characters from BRSR section")

            # Extract using BRSR-specific patterns
            data = extract_brsr_indicators(brsr_text)

            # Store in database
            stored = 0
            for indicator_id, value in data.items():
                existing = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    source='targeted_brsr_extraction',
                    data_key=indicator_id
                ).first()

                if existing:
                    existing.data_value = value
                else:
                    scraped_data = ScrapedData(
                        company_id=company_id,
                        year=year,
                        source='targeted_brsr_extraction',
                        data_key=indicator_id,
                        data_value=value
                    )
                    db.add(scraped_data)
                stored += 1

            db.commit()

            print(f"\n{'='*70}")
            print(f"TARGETED BRSR COMPLETE: {stored} new indicators")
            print(f"{'='*70}")

            return stored

    finally:
        db.close()

def extract_brsr_indicators(text: str) -> Dict[str, str]:
    """Extract indicators from BRSR text using structured patterns"""

    data = {}
    text = text.replace('\n', ' ')

    print("\nExtracting from BRSR structured data...")

    # BRSR Employee Data (very specific patterns)
    patterns = {
        # Employee/Worker Statistics
        'IMP-M11-I01': [  # Total Employees
            r'Total.*?Permanent.*?Employees.*?([0-9,]+)',
            r'Total.*?employees.*?FY.*?([0-9,]+)',
            r'Employees.*?Total.*?([0-9,]+)'
        ],
        'IMP-M11-I02': [  # Female Employees
            r'Female.*?([0-9,]+)',
            r'Women.*?([0-9,]+)',
            r'Female.*?Total.*?([0-9,]+)'
        ],
        'IMP-M11-I04': [  # Workers
            r'Total.*?Permanent.*?Workers.*?([0-9,]+)',
            r'Workers.*?Total.*?([0-9,]+)',
            r'Permanent.*?Workers.*?([0-9,]+)'
        ],
        'IMP-M11-I05': [  # Differently Abled
            r'Differently.*?abled.*?([0-9,]+)',
            r'Persons.*?with.*?disabilities.*?([0-9,]+)',
            r'PWD.*?([0-9,]+)'
        ],

        # Health & Safety
        'IMP-M12-I01': [  # LTIFR
            r'LTIFR.*?([0-9]+(?:\.[0-9]+)?)',
            r'Lost.*?Time.*?Injury.*?Rate.*?([0-9]+(?:\.[0-9]+)?)',
            r'Frequency.*?Rate.*?([0-9]+(?:\.[0-9]+)?)'
        ],
        'IMP-M12-I02': [  # Safety Training Hours
            r'safety.*?training.*?hours.*?([0-9,]+)',
            r'Health.*?safety.*?training.*?([0-9,]+)',
            r'Training.*?hours.*?([0-9,]+)'
        ],
        'IMP-M12-I03': [  # Fatalities
            r'Fatalities.*?([0-9]+)',
            r'Fatal.*?accidents.*?([0-9]+)',
            r'Deaths.*?([0-9]+)'
        ],
        'IMP-M12-I05': [  # Safety Assessments
            r'assessed.*?([0-9]+)%',
            r'Health.*?safety.*?practices.*?([0-9]+)%',
            r'plants.*?offices.*?assessed.*?([0-9]+)%'
        ],

        # Environmental Data
        'IMP-M05-I01': [  # Scope 1 Emissions
            r'Scope\s+1.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Direct.*?GHG.*?emissions.*?([0-9,]+)',
            r'Scope\s+1.*?([0-9,]+)\s*(?:tCO2e|Metric)'
        ],
        'IMP-M05-I02': [  # Scope 2 Emissions
            r'Scope\s+2.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Indirect.*?GHG.*?emissions.*?([0-9,]+)',
            r'Scope\s+2.*?([0-9,]+)\s*(?:tCO2e|Metric)'
        ],
        'IMP-M05-I03': [  # Scope 3 Emissions
            r'Scope\s+3.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Value.*?chain.*?emissions.*?([0-9,]+)',
            r'Scope\s+3.*?([0-9,]+)\s*(?:tCO2e|Metric)'
        ],

        # Energy
        'IMP-M06-I01': [  # Total Energy
            r'Total.*?energy.*?consumption.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Energy.*?consumed.*?([0-9,]+)',
            r'Total.*?energy.*?([0-9,]+)\s*(?:GJ|TJ)'
        ],
        'IMP-M06-I02': [  # Renewable Energy
            r'Renewable.*?energy.*?([0-9]+)%',
            r'renewable.*?sources.*?([0-9]+)%',
            r'Clean.*?energy.*?([0-9]+)%'
        ],

        # Water
        'IMP-M07-I01': [  # Water Withdrawal
            r'Total.*?water.*?withdrawal.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Water.*?withdrawn.*?([0-9,]+)',
            r'Water.*?consumption.*?([0-9,]+)\s*(?:KL|kilolitres)'
        ],
        'IMP-M07-I02': [  # Water Recycled
            r'Water.*?recycled.*?([0-9,]+)%',
            r'recycling.*?rate.*?([0-9,]+)%',
            r'recycled.*?water.*?([0-9,]+)'
        ],

        # Waste
        'IMP-M08-I01': [  # Waste Generated
            r'Total.*?waste.*?generated.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Waste.*?generated.*?([0-9,]+)',
            r'waste.*?([0-9,]+)\s*(?:Metric\s+tonnes|MT)'
        ],
        'IMP-M08-I02': [  # Waste Recycled
            r'Waste.*?recycled.*?([0-9,]+)%',
            r'recycling.*?([0-9,]+)%',
            r'waste.*?recovered.*?([0-9,]+)'
        ],
        'IMP-M08-I04': [  # Hazardous Waste
            r'Hazardous.*?waste.*?([0-9,]+(?:\.[0-9]+)?)',
            r'hazardous.*?([0-9,]+)\s*(?:Metric|tonnes)',
            r'Toxic.*?waste.*?([0-9,]+)'
        ],

        # Training
        'IMP-M13-I01': [  # Training Hours per Employee
            r'Average.*?training.*?hours.*?([0-9,]+(?:\.[0-9]+)?)',
            r'training.*?per.*?employee.*?([0-9,]+)',
            r'Average.*?training.*?([0-9,]+)\s*hours'
        ],
        'IMP-M13-I03': [  # Employees Trained
            r'employees.*?training.*?([0-9,]+)%',
            r'Training.*?coverage.*?([0-9,]+)%',
            r'Employees.*?trained.*?([0-9,]+)'
        ],

        # CSR
        'IMP-M14-I01': [  # CSR Spend
            r'CSR.*?expenditure.*?([0-9,]+(?:\.[0-9]+)?)',
            r'Amount.*?spent.*?CSR.*?([0-9,]+)',
            r'CSR.*?obligation.*?([0-9,]+)'
        ],
        'IMP-M14-I02': [  # CSR Projects
            r'Number.*?CSR.*?projects.*?([0-9,]+)',
            r'CSR.*?projects.*?([0-9,]+)',
            r'projects.*?undertaken.*?([0-9,]+)'
        ],

        # Governance
        'IMP-M02-I05': [  # Board Meetings
            r'Board.*?meetings.*?([0-9]+)',
            r'meetings.*?held.*?([0-9]+)',
            r'Board.*?met.*?([0-9]+)'
        ],
        'IMP-M16-I10': [  # Independent Directors
            r'Independent.*?Directors.*?([0-9]+)',
            r'Number.*?Independent.*?([0-9]+)',
            r'Independent.*?([0-9]+)'
        ],
        'IMP-M16-I11': [  # Women Directors
            r'Women.*?Directors.*?([0-9]+)',
            r'Female.*?directors.*?([0-9]+)',
            r'Women.*?Board.*?([0-9]+)'
        ]
    }

    # Extract with structured patterns
    found_count = 0
    for indicator_id, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and indicator_id not in data:
                value = match.group(1).strip().replace(',', '')

                # Validate numeric data
                if value and len(value) >= 1 and len(value) <= 50:
                    data[indicator_id] = value
                    print(f"  FOUND {indicator_id}: {value}")
                    found_count += 1
                    break

    print(f"\nExtracted {found_count} indicators from BRSR section")
    return data

if __name__ == "__main__":
    count = extract_brsr_structured_data(30, 2024)
    print(f"\nExtracted {count} new indicators from BRSR section")