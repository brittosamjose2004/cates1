#!/usr/bin/env python3
"""
BRSR (Business Responsibility & Sustainability Report) EXTRACTOR
Extracts structured ESG data from BRSR sections of annual reports
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import re
import PyPDF2
from typing import Dict, List
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

class BRSRExtractor:
    """Extracts ESG data from BRSR section"""

    def extract_from_brsr_section(self, pdf_path: Path) -> Dict[str, str]:
        """Extract from BRSR section (usually at end of annual report)"""

        data = {}

        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)

                # Find BRSR starting page (search from end of PDF where BRSR usually is)
                brsr_start = None
                total_pages = len(pdf.pages)

               # Start searching from 70% into the document
                start_search = int(total_pages * 0.7)

                for page_num in range(start_search, total_pages):
                    text = pdf.pages[page_num].extract_text()
                    # Multiple patterns to find BRSR section
                    if any(marker in text for marker in [
                        'SECTION A: GENERAL DISCLOSURES',
                        'Essential Indicators',
                        'Leadership Indicators',
                        'PRINCIPLE 1: Businesses should conduct',
                        'PRINCIPLE 2: Businesses should provide',
                        'PRINCIPLE 3: Businesses should'
                    ]):
                        brsr_start = page_num
                        print(f"    BRSR section found at page {brsr_start + 1}")
                        break

                if not brsr_start:
                    print("    BRSR section not found")
                    return data

                # Extract from BRSR pages (typically last 50-100 pages)
                all_brsr_text = ''
                pages_to_extract = min(100, len(pdf.pages) - brsr_start)

                for i in range(pages_to_extract):
                    all_brsr_text += pdf.pages[brsr_start + i].extract_text()

                print(f"    Extracted {pages_to_extract} BRSR pages, {len(all_brsr_text)} characters")

                # Apply BRSR-specific extraction patterns
                data = self._extract_brsr_indicators(all_brsr_text)

                return data

        except Exception as e:
            print(f"    BRSR extraction error: {str(e)}")
            return data

    def _extract_brsr_indicators(self, text: str) -> Dict[str, str]:
        """Extract ESG indicators from BRSR text"""

        data = {}

        # Clean text
        text = text.replace('\n', ' ')

        # BRSR-specific patterns (structured format)

        # Employee Data
        patterns_employees = {
            'IMP-M11-I01': [  # Total Permanent Employees
                r'Total.*?[Pp]ermanent.*?employees.*?([0-9,]+)',
                r'Permanent.*?Employees.*?Male.*?Female.*?Total.*?([0-9,]+)'
            ],
            'IMP-M11-I02': [  # Female Employees
                r'Female.*?employees.*?([0-9,]+)',
                r'Women.*?workforce.*?([0-9]+)%'
            ],
            'IMP-M11-I04': [  # Workers
                r'Total.*?[Ww]orkers.*?([0-9,]+)',
                r'Permanent.*?Workers.*?([0-9,]+)'
            ],
            'IMP-M11-I05': [  # Differently Abled
                r'Differently.*?abled.*?([0-9,]+)',
                r'Persons.*?with.*?disabilities.*?([0-9,]+)'
            ]
        }

        # Health & Safety Data
        patterns_ohs = {
            'IMP-M12-I01': [  # Lost Time Injury Frequency Rate
                r'LTIFR.*?([0-9]+(?:\.[0-9]+)?)',
                r'Lost.*?Time.*?Injury.*?Frequency.*?Rate.*?([0-9]+(?:\.[0-9]+)?)'
            ],
            'IMP-M12-I03': [  # Fatalities
                r'Fatalities.*?([0-9]+)',
                r'Fatal.*?accidents.*?([0-9]+)'
            ],
            'IMP-M12-I04': [  # Safety Training
                r'Health.*?safety.*?training.*?([0-9,]+).*?hours',
                r'Safety.*?training.*?([0-9,]+)'
            ],
            'IMP-M12-I05': [  # Safety Assessments
                r'Health.*?safety.*?practices.*?([0-9]+)%',
                r'that.*?were.*?assessed.*?([0-9]+)%'
            ]
        }

        # Environmental Data
        patterns_environment = {
            'IMP-M05-I01': [  # GHG Scope 1
                r'Scope\s+1.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:tCO2e|Metric tonnes)',
                r'Direct.*?GHG.*?emissions.*?([0-9,]+)'
            ],
            'IMP-M05-I02': [  # GHG Scope 2
                r'Scope\s+2.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:tCO2e|Metric tonnes)',
                r'Indirect.*?GHG.*?emissions.*?([0-9,]+)'
            ],
            'IMP-M05-I03': [  # GHG Scope 3
                r'Scope\s+3.*?emissions.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:tCO2e|Metric tonnes)'
            ],
            'IMP-M06-I01': [  # Energy Consumption
                r'Total.*?energy.*?consumption.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:GJ|Joules)',
                r'Energy.*?consumed.*?([0-9,]+)\s*(?:GJ|TJ)'
            ],
            'IMP-M06-I02': [  # Renewable Energy
                r'Energy.*?consumption.*?renewable.*?sources.*?([0-9]+(?:\.[0-9]+)?)\s*(?:%|GJ)',
                r'Renewable.*?energy.*?([0-9]+)%'
            ],
            'IMP-M07-I01': [  # Water Withdrawal
                r'Total.*?water.*?withdrawal.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:KL|kilolitres|m3)',
                r'Water.*?withdrawn.*?([0-9,]+)'
            ],
            'IMP-M07-I02': [  # Water Consumption
                r'Total.*?water.*?consumption.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:KL|kilolitres)',
                r'Water.*?consumed.*?([0-9,]+)'
            ],
            'IMP-M07-I03': [  # Water Discharge
                r'Total.*?water.*?discharge.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:KL|kilolitres)',
                r'Water.*?discharged.*?([0-9,]+)'
            ],
            'IMP-M08-I01': [  # Plastic Waste
                r'Plastic.*?waste.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric tonnes|MT)',
                r'E-waste.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric tonnes)'
            ],
            'IMP-M08-I02': [  # Waste Generated
                r'Total.*?waste.*?generated.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric tonnes|MT)',
                r'Waste.*?generated.*?([0-9,]+)'
            ],
            'IMP-M08-I03': [  # Waste Recovered
                r'Waste.*?recovered.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric tonnes|%)',
                r'Waste.*?recycled.*?([0-9,]+)'
            ]
        }

        # Training & Development
        patterns_training = {
            'IMP-M13-I01': [  # Training Hours
                r'Average.*?training.*?hours.*?employee.*?([0-9]+(?:\.[0-9]+)?)',
                r'Training.*?per.*?employee.*?([0-9,]+)\s*hours'
            ],
            'IMP-M13-I03': [  # Employees Trained
                r'(%.*?total.*?employees.*?training.*?([0-9]+))',
                r'employees.*?skill.*?upgradation.*?([0-9,]+)'
            ]
        }

        # CSR & Community
        patterns_csr = {
            'IMP-M14-I01': [  # CSR Spend
                r'CSR.*?(?:obligation|expenditure|spend).*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Crore|Cr)',
                r'Amount.*?required.*?to.*?be.*?spent.*?([0-9,]+(?:\.[0-9]+)?)'
            ],
            'IMP-M14-I02': [  # CSR Projects
                r'Number.*?of.*?CSR.*?projects.*?([0-9,]+)',
                r'CSR.*?projects.*?undertaken.*?([0-9,]+)'
            ]
        }

        # Governance
        patterns_governance = {
            'IMP-M16-I01': [  # Board Size
                r'Total.*?number.*?of.*?directors.*?([0-9]+)',
                r'Board.*?strength.*?([0-9]+)'
            ],
            'IMP-M16-I10': [  # Independent Directors
                r'Independent.*?Directors.*?([0-9]+)',
                r'Number.*?of.*?Independent.*?Directors.*?([0-9]+)'
            ],
            'IMP-M16-I11': [  # Women Directors
                r'Women.*?Directors.*?([0-9]+)',
                r'Female.*?directors.*?([0-9]+)'
            ],
            'IMP-M02-I05': [  # Board Meetings
                r'Number.*?of.*?(?:Board|meetings).*?held.*?([0-9]+)',
                r'Board.*?met.*?([0-9]+).*?times'
            ]
        }

        # Combine all patterns
        all_patterns = {
            **patterns_employees, **patterns_ohs, **patterns_environment,
            **patterns_training, **patterns_csr, **patterns_governance
        }

        # Extract using patterns
        for indicator_id, patterns in all_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and indicator_id not in data:
                    value = match.group(1).strip()

                    # Validate
                    value = re.sub(r'\s+', ' ', value)
                    if len(value) > 1 and len(value) < 100:
                        data[indicator_id] = value
                        print(f"    FOUND {indicator_id}: {value}")
                        break

        return data

def extract_brsr_data(company_id: int, year: int = 2024):
    """Main BRSR extraction function"""

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print("\n" + "="*70)
        print(f"BRSR SECTION EXTRACTION - {company.name}")
        print(f"Year: {year}")
        print("="*70)

        # Find PDF
        pdf_base = Path('data/annual_reports')
        folder_patterns = [
            company.name.upper().replace(' ', '_'),
            company.ticker if company.ticker else ''
        ]

        pdf_folder = None
        for pattern in folder_patterns:
            if not pattern:
                continue
            potential_folder = pdf_base / pattern
            if potential_folder.exists():
                pdf_folder = potential_folder
                break

        if not pdf_folder:
            print(f"No PDF folder found")
            return 0

        pdf_files = list(pdf_folder.glob('*.pdf'))
        if not pdf_files:
            print(f"No PDFs found")
            return 0

        # Extract BRSR data
        extractor = BRSRExtractor()
        brsr_data = extractor.extract_from_brsr_section(pdf_files[0])

        # Store in database
        stored = 0
        for indicator_id, value in brsr_data.items():
            existing = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year,
                source='brsr_section_extraction',
                data_key=indicator_id
            ).first()

            if existing:
                existing.data_value = value
            else:
                scraped_data = ScrapedData(
                    company_id=company_id,
                    year=year,
                    source='brsr_section_extraction',
                    data_key=indicator_id,
                    data_value=value
                )
                db.add(scraped_data)
            stored += 1

        db.commit()

        print("\n" + "="*70)
        print(f"BRSR EXTRACTION COMPLETE: {stored} indicators")
        print("="*70)

        return stored

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC
    company_id = 30
    year = 2024

    count = extract_brsr_data(company_id, year)
    print(f"\nFINAL: {count} indicators from BRSR section")
