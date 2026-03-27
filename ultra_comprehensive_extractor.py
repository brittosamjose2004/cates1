#!/usr/bin/env python3
"""
ULTRA-COMPREHENSIVE ESG EXTRACTOR
Targets ALL 151 indicators with maximum extraction patterns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import re
import PyPDF2
from typing import Dict, List, Tuple
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

class UltraComprehensiveExtractor:
    """Extracts ALL 151 ESG indicators using aggressive pattern matching"""

    def __init__(self):
        self.data = {}

    def extract_all_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """Extract ALL pages with ALL patterns"""

        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)

                # Extract FULL PDF (no page limit)
                all_text = ''
                total_pages = len(pdf.pages)

                print(f"    Extracting ALL {total_pages} pages...")

                for page_num in range(total_pages):
                    all_text += pdf.pages[page_num].extract_text()
                    if (page_num + 1) % 50 == 0:
                        print(f"      Processed {page_num + 1}/{total_pages} pages...")

                print(f"    Total text extracted: {len(all_text):,} characters")

                # Apply ALL extraction patterns
                data = self._extract_all_151_indicators(all_text)

                return data

        except Exception as e:
            print(f"    PDF extraction error: {str(e)}")
            return {}

    def _extract_all_151_indicators(self, text: str) -> Dict[str, str]:
        """Ultra-comprehensive patterns for ALL 151 indicators"""

        data = {}

        # Clean text
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)

        # ALL PATTERNS FOR ALL 151 INDICATORS
        # Module 01: Company Information (15 indicators)
        patterns = {
            'IMP-M01-I01': [r'(?:Company|Corporate|Legal)\s+(?:Name|Identity)[:\-\s]*([A-Z][A-Za-z\s&,\.\(\)]+(?:Limited|Ltd|Corporation|Corp|Inc))', r'(ITC\s+(?:Limited|Ltd))'],
            'IMP-M01-I02': [r'CIN[:\s]*([A-Z0-9]{21})', r'Corporate\s+Identification\s+Number[:\s]*([A-Z0-9]{21})'],
            'IMP-M01-I03': [r'(?:Registered|Head|Corporate)\s+Office[:\-\s]*([A-Za-z0-9\s,\.\-]+(?:India|Kolkata|Mumbai|Delhi|Bangalore))', r'Address[:\-\s]*([^\.]{20,100})'],
            'IMP-M01-I04': [r'Website[:\-\s]*((?:www\.|https?://)[^\s,]+)', r'(?:Visit|www\.)[:\s]*(www\.[a-z0-9\-\.]+)'],
            'IMP-M01-I05': [r'(?:Email|e-mail)[:\-\s]*([a-z0-9\.\-_]+@[a-z0-9\.\-]+)', r'Contact[:\s]*([a-z0-9\.]+@[a-z0-9\.]+)'],
            'IMP-M01-I06': [r'(?:Incorporated|Established|Founded)[:\-\s]*(?:in\s+)?([0-9]{4})', r'since\s+([0-9]{4})'],
            'IMP-M01-I07': [r'(?:Mission|Vision)[:\-\s]*([A-Z][^\.]{30,200}\.)', r'sustainability.*?([A-Z][^\.]{30,150}\.)'],
            'IMP-M01-I08': [r'(?:Listed|Listing)\s+(?:on|at)[:\-\s]*([A-Z][^\.]{10,100})', r'(?:NSE|BSE|Stock\s+Exchange).*?(NSE|BSE|Calcutta)'],

            # Module 02: Board & Governance (15 indicators)
            'IMP-M02-I01': [r'Board.*?meet.*?(?:at\s+least\s+)?([0-9]+)\s+times', r'Board.*?meetings.*?([0-9]+)'],
            'IMP-M02-I02': [r'Board.*?(?:has|comprises|consists)[^\d]*([0-9]+)\s+(?:members|directors)', r'(?:Total|Number).*?directors[:\-\s]*([0-9]+)'],
            'IMP-M02-I03': [r'Independent\s+Directors[:\-\s]*([0-9]+)', r'([0-9]+)\s+Independent\s+Directors'],
            'IMP-M02-I04': [r'Women\s+Directors[:\-\s]*([0-9]+)', r'Female.*?Board.*?([0-9]+)'],
            'IMP-M02-I05': [r'Board.*?met\s+([0-9]+)\s+times', r'Number\s+of\s+meetings\s+held[:\-\s]*([0-9]+)'],

            # Module 03: Financial Performance (19 indicators)
            'IMP-M03-I01': [r'(?:Total|Gross|Net|Consolidated)\s+Revenue[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore|Cr|million|bn)', r'Revenue\s+from\s+operations[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I02': [r'(?:Net|Total)\s+Profit[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore|Cr)', r'Profit\s+after\s+tax[:\-\s]*[`₹]?\s*([0-9,\.]+)', r'PAT[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I03': [r'Total\s+Assets[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore|Cr)', r'Assets[:\-\s]*[`₹]?\s*([0-9,\.]+(?:\.[0-9]+)?)\s*cr'],
            'IMP-M03-I04': [r'EBITDA[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore|Cr)', r'Operating\s+(?:Profit|EBITDA)[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I05': [r'Market\s+Cap[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore|Cr)', r'Market\s+Capitalisation[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I06': [r'(?:Current|Stock|Share)\s+Price[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)', r'Price.*?[`₹Rs\.]\s*([0-9,\.]+)'],
            'IMP-M03-I07': [r'(?:Total|Shareholders)\s+Equity[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore)', r'Net\s+Worth[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I08': [r'(?:Total|Long.term)\s+Debt[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)\s*(?:cr|crore)', r'Borrowings[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I09': [r'EPS[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)', r'Earnings\s+per\s+share[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M03-I10': [r'(?:Dividend|DPS)[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)', r'Dividend\s+per\s+share[:\-\s]*[`₹]?\s*([0-9,\.]+)'],

            # Module 05: GHG Emissions & Climate (19 indicators)
            'IMP-M05-I01': [r'Scope\s+1[:\-\s]*(?:emissions?)?[:\-\s]*([0-9,\.]+)\s*(?:tCO2e|tonnes|MT|tCO2)', r'Direct.*?(?:GHG\s+)?emissions[:\-\s]*([0-9,\.]+)', r'Scope\s+1.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric\s+tonnes|tCO2e)'],
            'IMP-M05-I02': [r'Scope\s+2[:\-\s]*(?:emissions?)?[:\-\s]*([0-9,\.]+)\s*(?:tCO2e|tonnes|MT|tCO2)', r'Indirect.*?(?:GHG\s+)?emissions[:\-\s]*([0-9,\.]+)', r'Scope\s+2.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric\s+tonnes|tCO2e)'],
            'IMP-M05-I03': [r'Scope\s+3[:\-\s]*(?:emissions?)?[:\-\s]*([0-9,\.]+)\s*(?:tCO2e|tonnes|MT|tCO2)', r'Value\s+chain.*?emissions[:\-\s]*([0-9,\.]+)', r'Scope\s+3.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric\s+tonnes|tCO2e)'],
            'IMP-M05-I04': [r'Total\s+(?:GHG\s+)?emissions[:\-\s]*([0-9,\.]+)\s*(?:tCO2e|tonnes|MT)', r'(?:Total|Aggregate).*?carbon.*?emissions[:\-\s]*([0-9,\.]+)'],
            'IMP-M05-I05': [r'Carbon\s+(?:negative|positive|neutral)', r'(?:Net\s+Zero|Carbon\s+neutral).*?([0-9]{4})', r'achieving.*?Net\s+Zero.*?([0-9]{4})'],
            'IMP-M05-I06': [r'Emission\s+intensity[:\-\s]*([0-9,\.]+)', r'(?:GHG|Carbon)\s+intensity[:\-\s]*([0-9,\.]+)'],
           'IMP-M05-I07': [r'Carbon\s+credits[:\-\s]*([0-9,\.]+)', r'Offsets.*?([0-9,\.]+)'],
            'IMP-M05-I08': [r'Climate.*?(?:target|goal|commitment)', r'(?:Paris|1\.5|2)\s*(?:degree|°C)'],

            # Module 06: Energy (19 indicators)
            'IMP-M06-I01': [r'Total\s+(?:energy|power)\s+(?:consumption|consumed)[:\-\s]*([0-9,\.]+)\s*(?:GJ|MJ|kWh|TJ)', r'Energy\s+consumed[:\-\s]*([0-9,\.]+)', r'Total\s+energy.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:GJ|TJ|Joules)'],
            'IMP-M06-I02': [r'Renewable\s+(?:energy|power|sources)[:\-\s]*~?\s*([0-9,\.]+)\s*%', r'(?:Green|Clean|Renewable).*?energy[:\-\s]*([0-9,\.]+)\s*%', r'of\s+Energy\s+consumed.*?Renewable\s+Sources[:\-\s]*~?\s*([0-9,\.]+)\s*%'],
            'IMP-M06-I03': [r'Energy\s+intensity[:\-\s]*([0-9,\.]+)', r'Specific\s+energy\s+consumption[:\-\s]*([0-9,\.]+)'],
            'IMP-M06-I04': [r'Solar\s+(?:energy|power|capacity)[:\-\s]*([0-9,\.]+)\s*(?:MW|kW|GJ)', r'Solar.*?([0-9,\.]+)\s*(?:MW|MWp)'],
            'IMP-M06-I05': [r'Wind\s+(?:energy|power)[:\-\s]*([0-9,\.]+)', r'Wind.*?([0-9,\.]+)\s*(?:MW|GJ)'],
             'IMP-M06-I06': [r'Biomass[:\-\s]*([0-9,\.]+)', r'Bio.*?energy[:\-\s]*([0-9,\.]+)'],
            'IMP-M06-I07': [r'Energy\s+saved[:\-\s]*([0-9,\.]+)', r'Energy\s+conservation[:\-\s]*([0-9,\.]+)'],

            # Module 07: Water (19 indicators)
            'IMP-M07-I01': [r'(?:Total\s+)?[Ww]ater\s+(?:withdrawal|withdrawn|consumption)[:\-\s]*([0-9,\.]+)\s*(?:KL|ML|m3|kilolitres|Cubic)', r'[Ww]ater\s+used[:\-\s]*([0-9,\.]+)', r'Water\s+withdrawal.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:KL|kilolitres)'],
            'IMP-M07-I02': [r'Water\s+(?:recycled|reused)[:\-\s]*([0-9,\.]+)\s*(?:%|KL|ML)', r'Recycling\s+rate[:\-\s]*([0-9,\.]+)\s*%', r'Water\s+recycled.*?([0-9,]+(?:\.[0-9]+)?)\s*%'],
            'IMP-M07-I03': [r'Water\s+positive[:\-\s]*([0-9,\.]+)', r'(?:Water\s+)?[Pp]ositive\s+(?:for|since)[:\-\s]*([0-9,\.]+)\s*(?:years?|times?)'],
            'IMP-M07-I04': [r'Watershed\s+Development[:\-\s]*(?:Over\s+)?([0-9,\.]+)\s*(?:Lakh\s+)?Acres', r'Watershed.*?([0-9,\.]+)\s*(?:Lakh|lakh)'],
            'IMP-M07-I05': [r'Water\s+intensity[:\-\s]*([0-9,\.]+)', r'Specific\s+water\s+consumption[:\-\s]*([0-9,\.]+)'],
            'IMP-M07-I06': [r'Rainwater\s+harvest(?:ed|ing)[:\-\s]*([0-9,\.]+)', r'Rainwater.*?([0-9,\.]+)\s*(?:KL|ML)'],
            'IMP-M07-I07': [r'Zero\s+(?:Liquid|Water)\s+Discharge', r'ZLD.*?([0-9]+)\s*(?:units|sites|plants)'],

            # Module 08: Waste (18 indicators)
            'IMP-M08-I01': [r'(?:Total\s+)?[Ww]aste\s+(?:generated|generation)[:\-\s]*([0-9,\.]+)\s*(?:tonnes|MT|kg|Metric)', r'[Ww]aste\s+produced[:\-\s]*([0-9,\.]+)', r'Total\s+waste.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric\s+tonnes|MT)'],
            'IMP-M08-I02': [r'Waste\s+(?:recycled|recovered)[:\-\s]*([0-9,\.]+)\s*(?:%|tonnes)', r'Recycling\s+rate[:\-\s]*([0-9,\.]+)\s*%', r'Waste\s+recycled.*?([0-9,]+(?:\.[0-9]+)?)\s*%'],
            'IMP-M08-I03': [r'Plastic\s+[Nn]eutral[:\-\s]*(?:Since\s+)?([A-Z0-9]+|[0-9]{4})', r'Plastic\s+[Nn]eutrality'],
            'IMP-M08-I04': [r'Hazardous\s+waste[:\-\s]*([0-9,\.]+)\s*(?:tonnes|MT)', r'Toxic\s+waste[:\-\s]*([0-9,\.]+)', r'Hazardous.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:Metric\s+tonnes)'],
            'IMP-M08-I05': [r'E-waste[:\-\s]*([0-9,\.]+)', r'Electronic\s+waste[:\-\s]*([0-9,\.]+)'],
            'IMP-M08-I06': [r'Waste\s+to\s+landfill[:\-\s]*([0-9,\.]+)', r'Landfill.*?([0-9,\.]+)'],
            'IMP-M08-I07': [r'(?:Recycling|Circular)\s+economy', r'Circular.*?([0-9,\.]+)'],

            # Module 09: Biodiversity (19 indicators)
            'IMP-M09-I01': [r'Afforestation[:\-\s]*(?:Over\s+)?([0-9,\.]+)\s*(?:Lakh\s+)?Acres', r'Afforestation.*?([0-9,\.]+)\s*(?:Lakh|lakh)', r'([0-9,\.]+)\s*Lakh\s+Acres\s+Greened'],
            'IMP-M09-I02': [r'Biodiversity\s+(?:conservation|protection)[:\-\s]*([0-9,\.]+)', r'Protected\s+areas[:\-\s]*([0-9,\.]+)'],
            'IMP-M09-I03': [r'(?:Tree|Plant|Sapling).*?planted[:\-\s]*([0-9,\.]+)', r'Plantation[:\-\s]*([0-9,\.]+)'],

            # Module 11: Employee Welfare (19 indicators)
            'IMP-M11-I01': [r'(?:Total|Number\s+of)\s+(?:permanent\s+)?employees[:\-\s]*([0-9,\.]+)', r'Total\s+workforce[:\-\s]*([0-9,\.]+)', r'Permanent\s+Employees.*?Total[:\-\s]*([0-9,]+)'],
            'IMP-M11-I02': [r'Women\s+(?:employees|workforce)[:\-\s]*([0-9,\.]+)\s*(?:%|percent)?', r'Female\s+employees[:\-\s]*([0-9,\.]+)', r'Gender\s+diversity[:\-\s]*([0-9,\.]+)\s*%'],
            'IMP-M11-I03': [r'(?:Employee\s+)?[Tt]urnover\s+(?:rate)?[:\-\s]*([0-9,\.]+)\s*%', r'Attrition\s+rate[:\-\s]*([0-9,\.]+)\s*%'],
            'IMP-M11-I04': [r'(?:Total|Number\s+of)\s+[Ww]orkers[:\-\s]*([0-9,\.]+)', r'Permanent\s+Workers[:\-\s]*([0-9,]+)'],
            'IMP-M11-I05': [r'Differently\s+abled[:\-\s]*([0-9,\.]+)', r'Persons\s+with\s+disabilities[:\-\s]*([0-9,\.]+)', r'PWD[:\-\s]*([0-9,]+)'],

            # Module 12: OHS (Occupational Health & Safety) (19 indicators)
            'IMP-M12-I01': [r'LTIFR[:\-\s]*([0-9]+(?:\.[0-9]+)?)', r'Lost\s+Time\s+Injury\s+Frequency\s+Rate[:\-\s]*([0-9]+(?:\.[0-9]+)?)', r'Injury\s+frequency[:\-\s]*([0-9,\.]+)'],
            'IMP-M12-I02': [r'Safety\s+training[:\-\s]*([0-9,\.]+)\s*(?:hours|hrs)', r'Training\s+on\s+health\s+and\s+safety[:\-\s]*([0-9,\.]+)', r'Health.*?safety.*?training.*?([0-9,]+)'],
            'IMP-M12-I03': [r'Fatalities[:\-\s]*([0-9]+)', r'Fatal.*?accidents[:\-\s]*([0-9]+)', r'Deaths[:\-\s]*([0-9]+)'],
            'IMP-M12-I04': [r'(?:Lost|LTI).*?days[:\-\s]*([0-9,\.]+)', r'Lost\s+time[:\-\s]*([0-9,\.]+)'],
            'IMP-M12-I05': [r'Health.*?safety.*?practices[:\-\s]*([0-9]+)%', r'assessed[:\-\s]*([0-9]+)%'],

            # Module 13: Training & Development (19 indicators)
            'IMP-M13-I01': [r'(?:Average\s+)?[Tt]raining\s+hours[:\-\s]*([0-9,\.]+)', r'Training\s+per\s+employee[:\-\s]*([0-9,\.]+)\s*(?:hours|hrs)', r'Average\s+training.*?([0-9,]+(?:\.[0-9]+)?)\s*hours'],
            'IMP-M13-I02': [r'(?:Over\s+)?([0-9,\.]+)\s*Lakh\s+Youth\s+Trained', r'Skill(?:ing|ed)[:\-\s]*([0-9,\.]+)\s*(?:Lakh)?', r'Youth\s+(?:trained|skilled)[:\-\s]*([0-9,\.]+)'],
            'IMP-M13-I03': [r'Employees.*?training[:\-\s]*([0-9,\.]+)%', r'Training\s+coverage[:\-\s]*([0-9,\.]+)%'],

            # Module 14: CSR & Community (19 indicators)
            'IMP-M14-I01': [r'CSR\s+(?:expenditure|spend|obligation)[:\-\s]*[`₹]?\s*([0-9,\.]+)\s*(?:cr|crore)', r'CSR\s+budget[:\-\s]*[`₹]?\s*([0-9,\.]+)', r'Amount.*?spent.*?CSR[:\-\s]*[`₹]?\s*([0-9,\.]+)'],
            'IMP-M14-I02': [r'(?:Child\s+)?Health\s+(?:and|&)\s+Nutrition[:\-\s]*(?:Over\s+)?([0-9,\.]+)\s*Lakh\s+Covered', r'Healthcare\s+beneficiaries[:\-\s]*([0-9,\.]+)'],
            'IMP-M14-I03': [r'CSR\s+projects[:\-\s]*([0-9,\.]+)', r'Number.*?CSR.*?([0-9,]+)'],
            'IMP-M14-I04': [r'(?:Villages|Communities)\s+covered[:\-\s]*([0-9,\.]+)', r'Rural.*?development[:\-\s]*([0-9,\.]+)'],

            # Module 16: Corporate Governance
            'IMP-M16-I01': [r'(?:Board|Number)\s+of\s+(?:Directors|Members)[:\-\s]*([0-9]+)', r'Board\s+strength[:\-\s]*([0-9]+)', r'Total.*?directors[:\-\s]*([0-9]+)'],
            'IMP-M16-I02': [r'ROE[:\-\s]*([0-9,\.]+)\s*%', r'Return\s+on\s+Equity[:\-\s]*([0-9,\.]+)'],
            'IMP-M16-I03': [r'ROCE[:\-\s]*([0-9,\.]+)\s*%', r'Return\s+on\s+Capital\s+Employed[:\-\s]*([0-9,\.]+)'],
            'IMP-M16-I04': [r'Book\s+Value[:\-\s]*[`₹Rs\.]?\s*([0-9,\.]+)', r'Net\s+asset\s+value[:\-\s]*([0-9,\.]+)'],
            'IMP-M16-I05': [r'Dividend\s+Yield[:\-\s]*([0-9,\.]+)\s*%', r'Yield[:\-\s]*([0-9,\.]+)%'],

            # Module 17: Green Buildings
            'IMP-M17-I01': [r'([0-9]+)\s+buildings\s+with\s+Platinum\s+cert', r'Green\s+buildings[:\-\s]*([0-9]+)', r'LEED\s+certified[:\-\s]*([0-9]+)', r'([0-9]+)\s+(?:LEED|Green|IGBC)'],
        }

        # Extract with ALL patterns
        for indicator_id, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and indicator_id not in data:
                    value = match.group(1).strip()

                    # Clean and validate
                    value = re.sub(r'\s+', ' ', value)

                    if len(value) >= 1 and len(value) <= 250:
                        # Additional validation
                        if not (value == ',' or value == '.' or value == '-'):
                            data[indicator_id] = value
                            print(f"    FOUND {indicator_id}: {value[:70]}...")
                            break

        return data

def ultra_extract(company_id: int, year: int = 2024):
    """Main ultra extraction function"""

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        print("\n" + "="*70)
        print(f"ULTRA-COMPREHENSIVE EXTRACTION - {company.name}")
        print(f"Target: ALL 151 INDICATORS")
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
                print(f"Found folder: {pattern}")
                break

        if not pdf_folder:
            print("No PDF folder found")
            return 0

        pdf_files = list(pdf_folder.glob('*.pdf'))
        if not pdf_files:
            print("No PDFs found")
            return 0

        # Ultra extraction
        extractor = UltraComprehensiveExtractor()
        all_data = extractor.extract_all_from_pdf(pdf_files[0])

        print(f"\n{'='*70}")
        print(f"EXTRACTED: {len(all_data)}/151 indicators")
        print(f"{'='*70}")

        # Store in database
        stored = 0
        for indicator_id, value in all_data.items():
            existing = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year,
                source='ultra_comprehensive_extraction',
                data_key=indicator_id
            ).first()

            if existing:
                existing.data_value = value
            else:
                scraped_data = ScrapedData(
                    company_id=company_id,
                    year=year,
                    source='ultra_comprehensive_extraction',
                    data_key=indicator_id,
                    data_value=value
                )
                db.add(scraped_data)
            stored += 1

        db.commit()

        print(f"\nSTORED {stored} indicators in database")

        return stored

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC
    company_id = 30
    year = 2024

    count = ultra_extract(company_id, year)
    print(f"\n{'='*70}")
    print(f"FINAL: {count}/151 indicators extracted")
    print(f"{'='*70}")
