#!/usr/bin/env python3
"""
REAL DOCUMENT EXTRACTOR
Extracts actual ESG data from real PDF documents in the data/ folder.
Uses existing annual reports to populate the 151 ESG indicators.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
import re
from typing import Dict, List, Optional
import PyPDF2
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData
from backend.processor.csv_loader import ImpactreeCSVLoader

class RealDocumentExtractor:
    """Extract real ESG data from actual company documents"""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.data_dir = self.project_root / "data"
        self.report_roots = [
            self.data_dir / "annual_reports",
            self.project_root / "scrapper_new-main" / "downloads" / "nseindia.com",
            self.project_root / "scrapper_new-main" / "downloads" / "annualreports.com",
        ]
        self.extraction_patterns = self._define_esg_patterns()
        self.indicator_defs = ImpactreeCSVLoader.get_all_indicators()
        self.indicator_ids = [ind.get("indicator_id", "") for ind in self.indicator_defs if ind.get("indicator_id")]
        self.stopwords = {
            "the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "has", "have",
            "will", "shall", "into", "about", "your", "their", "where", "which", "what", "when", "year",
            "entity", "company", "indicator", "value", "data", "report", "under", "through", "based",
            "such", "than", "also", "other", "each", "more", "less", "been", "being", "between",
        }

    def _define_esg_patterns(self) -> Dict[str, List[str]]:
        """Define regex patterns to extract ESG data from real documents"""
        return {
            # M01 - General & Organizational Profile
            'IMP-M01-I01': [
                r"Company.*Name[:\-\s]*([A-Z][A-Za-z\s&,\.]+)",
                r"Corporate.*Identity.*Number[:\-\s]*([A-Z0-9]+)",
                r"CIN[:\-\s]*([A-Z0-9]+)",
                r"Registration.*Number[:\-\s]*([A-Z0-9]+)"
            ],
            'IMP-M01-I02': [
                r"Principal.*Business.*Activities[:\-\s]*([A-Za-z\s,\.]+)",
                r"Nature.*of.*Business[:\-\s]*([A-Za-z\s,\.]+)",
                r"Industry[:\-\s]*([A-Za-z\s,\.]+)"
            ],
            'IMP-M01-I03': [
                r"Number.*of.*locations.*where.*plants.*and/or.*operations/offices.*of.*the.*entity.*are.*situated[:\-\s]*([0-9,]+)",
                r"Manufacturing.*facilities[:\-\s]*([0-9,]+)",
                r"Office.*locations[:\-\s]*([0-9,]+)"
            ],

            # M03 - Financial Performance
            'IMP-M03-I01': [
                r"Total.*revenue.*from.*operations[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?",
                r"Revenue.*from.*operations[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?",
                r"Net.*revenue[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?"
            ],
            'IMP-M03-I02': [
                r"Net.*profit.*after.*tax[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?",
                r"Profit.*after.*tax[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?",
                r"PAT[:\-\s]*(?:INR|Rs\.?|₹)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|million|billion)?"
            ],

            # M05 - Climate Change & GHG Emissions
            'IMP-M05-I01': [
                r"Total.*Scope.*1.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?",
                r"Scope.*1.*GHG.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?",
                r"Direct.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?"
            ],
            'IMP-M05-I02': [
                r"Total.*Scope.*2.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?",
                r"Scope.*2.*GHG.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?",
                r"Indirect.*emissions[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tCO2e|tonnes?\s*CO2|MT\s*CO2)?"
            ],

            # M06 - Energy Management
            'IMP-M06-I01': [
                r"Total.*energy.*consumption[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ)?",
                r"Energy.*consumed[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ)?",
                r"Electricity.*consumption[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ)?"
            ],
            'IMP-M06-I02': [
                r"Renewable.*energy.*consumption[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ|%)?",
                r"Clean.*energy[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ|%)?",
                r"Solar.*energy[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:kWh|MWh|GJ|TJ)?"
            ],

            # M07 - Water Stewardship
            'IMP-M07-I01': [
                r"Total.*water.*consumption[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:liters|kiloliters|KL|ML)?",
                r"Water.*consumed[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:liters|kiloliters|KL|ML)?",
                r"Fresh.*water.*consumption[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:liters|kiloliters|KL|ML)?"
            ],

            # M08 - Waste Management
            'IMP-M08-I01': [
                r"Total.*waste.*generated[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tonnes?|MT|kg|tons)?",
                r"Waste.*generated[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tonnes?|MT|kg|tons)?",
                r"Solid.*waste[:\-\s]*([0-9,]+\.?[0-9]*)\s*(?:tonnes?|MT|kg|tons)?"
            ],

            # M15 - Human Rights & Labor Practices
            'IMP-M15-I01': [
                r"Total.*number.*of.*employees[:\-\s]*([0-9,]+)",
                r"Employee.*strength[:\-\s]*([0-9,]+)",
                r"Workforce[:\-\s]*([0-9,]+)",
                r"Total.*employees[:\-\s]*([0-9,]+)"
            ],
            'IMP-M15-I02': [
                r"Women.*employees[:\-\s]*([0-9,]+)",
                r"Female.*workforce[:\-\s]*([0-9,]+)",
                r"Gender.*diversity[:\-\s]*([0-9,]+\.?[0-9]*)%"
            ]
        }

    def extract_from_company_pdfs(self, company_id: int, year: int) -> Dict[str, str]:
        """Extract ESG data from real PDF documents for a specific company"""

        db = get_session()
        try:
            company = db.query(Company).filter_by(id=company_id).first()
            if not company:
                print(f"Company {company_id} not found")
                return {}

            print(f"\n[SEARCH] REAL PDF EXTRACTION")
            print(f"Company: {company.name}")
            print(f"Year: {year}")
            print("=" * 60)

            extracted_data = {}
            all_chunks: List[str] = []

            # Find company folder in data directory
            company_folders = self._find_company_folders(company.name, year)

            for folder_path in company_folders:
                print(f"[FOLDER] Found company folder: {folder_path}")

                # Extract only target-year files (exact year, else nearest past year).
                all_pdfs = list(folder_path.glob("*.pdf"))
                pdf_files = self._select_pdfs_for_year(all_pdfs, year)
                print(f"[PDF] Selected {len(pdf_files)} PDF file(s) for target year {year}")

                for pdf_file in pdf_files:
                    print(f"   Processing: {pdf_file.name}")
                    pdf_data, chunks = self._extract_from_pdf(pdf_file)
                    extracted_data.update(pdf_data)
                    all_chunks.extend(chunks)

            # Fill remaining indicators with best real text snippet from downloaded reports.
            missing_ids = [ind_id for ind_id in self.indicator_ids if ind_id and ind_id not in extracted_data]
            if all_chunks and missing_ids:
                snippet_fills = self._extract_by_text_similarity(all_chunks, missing_ids)
                extracted_data.update(snippet_fills)

            print(f"\n[SUCCESS] Extraction completed: {len(extracted_data)} indicators extracted")
            print(f"Indicators found: {list(extracted_data.keys())[:10]}...")  # Show first 10

            return extracted_data

        finally:
            db.close()

    def _find_company_folders(self, company_name: str, year: int) -> List[Path]:
        """Find folders that match the company name"""
        folders = []
        available_roots = [root for root in self.report_roots if root.exists()]
        if not available_roots:
            print("[ERROR] No report roots found")
            return folders

        # Clean company name for matching
        clean_name = company_name.upper().replace(" ", "_").replace(".", "").replace(",", "")

        for root in available_roots:
            for folder in root.iterdir():
                if not folder.is_dir():
                    continue

                folder_clean = folder.name.upper().replace(" ", "_").replace(".", "").replace(",", "")

                # Various matching strategies
                if (clean_name in folder_clean or
                    folder_clean in clean_name or
                    self._fuzzy_match(clean_name, folder_clean)):
                    # Prefer year subfolder when present (new company/year organization).
                    year_dir = folder / str(year)
                    chosen = year_dir if year_dir.exists() else folder
                    folders.append(chosen)
                    print(f"[SUCCESS] Matched '{company_name}' with folder '{chosen}'")

        if not folders:
            print(f"[ERROR] No matching folders found for '{company_name}'")
            sample = []
            for root in available_roots:
                sample.extend([f.name for f in root.iterdir() if f.is_dir()][:5])
            print(f"Available folders: {sample[:10]}")

        return folders

    def _extract_year_from_filename(self, name: str) -> Optional[int]:
        """Extract a 4-digit year token from file name/path if present."""
        m = re.search(r"(19|20)\d{2}", name or "")
        if not m:
            return None
        try:
            return int(m.group(0))
        except Exception:
            return None

    def _select_pdfs_for_year(self, pdf_files: List[Path], target_year: int) -> List[Path]:
        """Pick only PDFs relevant to requested year; never process all years together."""
        if not pdf_files:
            return []

        annual_like = [
            p for p in pdf_files
            if any(k in p.name.lower() for k in ("annual report", "annual_report", "integrated annual"))
        ]
        candidates = annual_like if annual_like else pdf_files

        tagged: List[tuple[Path, Optional[int]]] = []
        for p in candidates:
            tagged.append((p, self._extract_year_from_filename(str(p))))

        exact = [p for p, y in tagged if y == target_year]
        if exact:
            return exact

        past_years = sorted({y for _, y in tagged if y is not None and y <= target_year}, reverse=True)
        if past_years:
            chosen_year = past_years[0]
            return [p for p, y in tagged if y == chosen_year]

        with_mtime = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
        return with_mtime[:1]

    def _fuzzy_match(self, name1: str, name2: str) -> bool:
        """Simple fuzzy matching for company names"""
        # Extract key words (remove common words)
        common_words = {'LIMITED', 'LTD', 'PRIVATE', 'PVT', 'COMPANY', 'CORP', 'TECHNOLOGIES', 'TECH'}

        words1 = set(name1.split()) - common_words
        words2 = set(name2.split()) - common_words

        if not words1 or not words2:
            return False

        # If any significant word matches
        return len(words1.intersection(words2)) > 0

    def _extract_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """Extract ESG data from a single PDF using regex + return searchable chunks."""
        extracted = {}
        chunks: List[str] = []

        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                # Read text from all pages (limit to first 50 pages for performance)
                text = ""
                max_pages = min(50, len(pdf_reader.pages))

                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    text += (page.extract_text() or "") + "\n"

                chunks = self._build_text_chunks(text)

                # Apply extraction patterns
                for indicator_id, patterns in self.extraction_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            value = match.group(1).strip()
                            if value and len(value) > 1:  # Valid extraction
                                extracted[indicator_id] = value
                                print(f"      [SUCCESS] {indicator_id}: {value}")
                                break  # Use first successful pattern

        except Exception as e:
            print(f"      [ERROR] Error reading PDF {pdf_path}: {str(e)}")

        return extracted, chunks

    def _build_text_chunks(self, text: str) -> List[str]:
        """Create searchable chunks from PDF text for indicator-snippet mapping."""
        if not text:
            return []

        # Keep printable-ish lines and merge into medium chunks.
        raw_lines = [ln.strip() for ln in text.splitlines() if ln and len(ln.strip()) >= 40]
        chunks: List[str] = []
        current = ""
        for ln in raw_lines:
            piece = re.sub(r"\s+", " ", ln)
            if len(current) + len(piece) + 1 <= 420:
                current = (current + " " + piece).strip()
            else:
                if len(current) >= 80:
                    chunks.append(current)
                current = piece

        if len(current) >= 80:
            chunks.append(current)

        return chunks

    def _keyword_tokens(self, text: str) -> set[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", (text or "").lower())
        return {w for w in words if w not in self.stopwords and not w.isdigit()}

    def _extract_by_text_similarity(self, chunks: List[str], missing_ids: List[str]) -> Dict[str, str]:
        """Map each missing indicator to best-matching real snippet from document text."""
        by_id = {ind.get("indicator_id", ""): ind for ind in self.indicator_defs}
        result: Dict[str, str] = {}

        chunk_tokens = [(ch, self._keyword_tokens(ch)) for ch in chunks]

        for indicator_id in missing_ids:
            ind = by_id.get(indicator_id)
            if not ind:
                continue

            q = f"{ind.get('indicator_name', '')} {ind.get('question', '')} {ind.get('module_name', '')}"
            q_tokens = self._keyword_tokens(q)
            if not q_tokens:
                continue

            best_chunk = ""
            best_score = 0
            for ch, toks in chunk_tokens:
                overlap = len(q_tokens.intersection(toks))
                if overlap > best_score:
                    best_score = overlap
                    best_chunk = ch

            # In strict scraped-only mode we still want complete coverage, so allow
            # the best available real snippet when there is at least 1 keyword hit.
            if best_chunk and best_score >= 1:
                result[indicator_id] = best_chunk[:500]

        if result:
            print(f"[SIMILARITY] Filled {len(result)} indicators from real text snippets")

        return result

    def store_extracted_data(self, company_id: int, year: int, extracted_data: Dict[str, str]) -> int:
        """Store extracted data in ScrapedData table"""
        if not extracted_data:
            return 0

        db = get_session()
        stored_count = 0

        try:
            for indicator_id, value in extracted_data.items():
                # Check if already exists
                existing = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    source='real_pdf_extraction',
                    data_key=indicator_id
                ).first()

                if existing:
                    # Update existing
                    existing.data_value = value
                    print(f"[UPDATE] Updated {indicator_id}: {value}")
                else:
                    # Create new
                    scraped_data = ScrapedData(
                        company_id=company_id,
                        year=year,
                        source='real_pdf_extraction',
                        data_key=indicator_id,
                        data_value=value
                    )
                    db.add(scraped_data)
                    print(f"[ADD] Added {indicator_id}: {value}")

                stored_count += 1

            db.commit()
            print(f"\n[SAVE] Stored {stored_count} extracted values in database")

        except Exception as e:
            db.rollback()
            print(f"[ERROR] Error storing data: {str(e)}")
        finally:
            db.close()

        return stored_count

def extract_real_data_for_company(company_id: int, year: int = 2024) -> int:
    """Main function to extract real data from company documents"""
    extractor = RealDocumentExtractor()

    # Extract data from PDFs
    extracted_data = extractor.extract_from_company_pdfs(company_id, year)

    # Store in database
    if extracted_data:
        return extractor.store_extracted_data(company_id, year, extracted_data)
    else:
        print("[ERROR] No data extracted from documents")
        return 0

if __name__ == "__main__":
    # Test extraction
    print("[TEST] TESTING REAL PDF DOCUMENT EXTRACTION")
    print("=" * 80)

    # Test with different companies
    test_companies = [1, 2, 4, 17]  # HCL, Infosys, TCS, Hindustan Unilever

    for company_id in test_companies:
        count = extract_real_data_for_company(company_id, 2024)
        print(f"Company {company_id}: {count} indicators extracted\n")