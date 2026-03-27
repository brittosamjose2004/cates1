#!/usr/bin/env python3
"""
ENHANCED DYNAMIC PATTERN SOURCES - COMPREHENSIVE DOCUMENT SCRAPING
Downloads and scrapes ALL online resources: Annual Reports, BRSR, Sustainability Reports, etc.
Extracts indicator values from real documents instead of just web pattern matching
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from bs4 import BeautifulSoup
import time
import re
import PyPDF2
import io
from urllib.parse import urljoin, urlparse
from backend.database.db import get_session
from backend.database.models import ScrapedData, Company

class ComprehensiveDocumentScraper:
    """Downloads and scrapes comprehensive documents for real indicator extraction"""

    def __init__(self, company_name: str, year: int):
        self.company_name = company_name
        self.year = year
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def download_and_scrape_all_documents(self, company_id: int):
        """Download and scrape ALL available documents for comprehensive indicator extraction"""

        print(f"=" * 100)
        print(f"COMPREHENSIVE DOCUMENT SCRAPING FOR {self.company_name} {self.year}")
        print(f"Downloading: Annual Reports, BRSR, Sustainability Reports, ESG Studies")
        print(f"=" * 100)

        total_indicators = 0

        # 1. Download and scrape Annual Reports
        annual_indicators = self._download_annual_reports(company_id)
        total_indicators += annual_indicators

        # 2. Download and scrape BRSR Reports
        brsr_indicators = self._download_brsr_reports(company_id)
        total_indicators += brsr_indicators

        # 3. Download and scrape Sustainability Reports
        sustainability_indicators = self._download_sustainability_reports(company_id)
        total_indicators += sustainability_indicators

        # 4. Download and scrape ESG Studies & Reports
        esg_indicators = self._download_esg_studies(company_id)
        total_indicators += esg_indicators

        # 5. Download and scrape Investor Presentations
        presentation_indicators = self._download_investor_presentations(company_id)
        total_indicators += presentation_indicators

        print(f"\n" + "=" * 100)
        print(f"COMPREHENSIVE DOCUMENT SCRAPING COMPLETE")
        print(f"Total indicators extracted from ALL documents: {total_indicators}")
        print(f"=" * 100)

        return total_indicators

    def _download_annual_reports(self, company_id: int):
        """Download and extract data from annual reports"""
        print(f"\n1. DOWNLOADING ANNUAL REPORTS...")

        try:
            # Search for annual reports
            annual_report_urls = self._search_annual_reports()
            indicators_found = 0

            for i, url in enumerate(annual_report_urls[:3], 1):  # Process top 3 results
                print(f"   [{i}] Processing: {url[:60]}...")

                try:
                    # Download PDF
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):

                        # Extract text from PDF
                        pdf_text = self._extract_pdf_text(response.content)
                        if pdf_text:
                            # Extract indicators from text
                            extracted = self._extract_indicators_from_text(
                                pdf_text,
                                company_id,
                                f'annual_report_{self.year}_{i}',
                                'Annual Report'
                            )
                            indicators_found += extracted
                            print(f"       SUCCESS: {extracted} indicators extracted")

                except Exception as e:
                    print(f"       ERROR: {str(e)[:50]}...")
                    continue

                time.sleep(2)  # Rate limiting

            print(f"   ANNUAL REPORTS TOTAL: {indicators_found} indicators")
            return indicators_found

        except Exception as e:
            print(f"   Annual reports error: {str(e)[:50]}...")
            return 0

    def _download_brsr_reports(self, company_id: int):
        """Download and extract data from BRSR reports"""
        print(f"\n2. DOWNLOADING BRSR REPORTS...")

        try:
            # Search for BRSR reports
            brsr_urls = self._search_brsr_reports()
            indicators_found = 0

            for i, url in enumerate(brsr_urls[:2], 1):  # Process top 2 results
                print(f"   [{i}] Processing BRSR: {url[:60]}...")

                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:

                        # Handle different file types
                        content_type = response.headers.get('content-type', '')

                        if 'application/pdf' in content_type:
                            pdf_text = self._extract_pdf_text(response.content)
                            if pdf_text:
                                extracted = self._extract_indicators_from_text(
                                    pdf_text,
                                    company_id,
                                    f'brsr_report_{self.year}_{i}',
                                    'BRSR Report'
                                )
                                indicators_found += extracted

                        elif 'text/html' in content_type:
                            # HTML page with BRSR data
                            html_text = self._extract_html_text(response.content)
                            if html_text:
                                extracted = self._extract_indicators_from_text(
                                    html_text,
                                    company_id,
                                    f'brsr_web_{self.year}_{i}',
                                    'BRSR Web Data'
                                )
                                indicators_found += extracted

                        print(f"       SUCCESS: {extracted if 'extracted' in locals() else 0} BRSR indicators")

                except Exception as e:
                    print(f"       ERROR: {str(e)[:50]}...")
                    continue

                time.sleep(2)

            print(f"   BRSR REPORTS TOTAL: {indicators_found} indicators")
            return indicators_found

        except Exception as e:
            print(f"   BRSR reports error: {str(e)[:50]}...")
            return 0

    def _download_sustainability_reports(self, company_id: int):
        """Download and extract data from sustainability reports"""
        print(f"\n3. DOWNLOADING SUSTAINABILITY REPORTS...")

        try:
            sustainability_urls = self._search_sustainability_reports()
            indicators_found = 0

            for i, url in enumerate(sustainability_urls[:3], 1):
                print(f"   [{i}] Processing sustainability: {url[:60]}...")

                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:

                        if 'application/pdf' in response.headers.get('content-type', ''):
                            pdf_text = self._extract_pdf_text(response.content)
                            if pdf_text:
                                extracted = self._extract_indicators_from_text(
                                    pdf_text,
                                    company_id,
                                    f'sustainability_{self.year}_{i}',
                                    'Sustainability Report'
                                )
                                indicators_found += extracted
                                print(f"       SUCCESS: {extracted} sustainability indicators")

                except Exception as e:
                    print(f"       ERROR: {str(e)[:50]}...")
                    continue

                time.sleep(2)

            print(f"   SUSTAINABILITY REPORTS TOTAL: {indicators_found} indicators")
            return indicators_found

        except Exception as e:
            print(f"   Sustainability reports error: {str(e)[:50]}...")
            return 0

    def _download_esg_studies(self, company_id: int):
        """Download and extract data from ESG studies and research"""
        print(f"\n4. DOWNLOADING ESG STUDIES & RESEARCH...")

        try:
            esg_urls = self._search_esg_studies()
            indicators_found = 0

            for i, url in enumerate(esg_urls[:2], 1):
                print(f"   [{i}] Processing ESG study: {url[:60]}...")

                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:

                        content_type = response.headers.get('content-type', '')

                        if 'application/pdf' in content_type:
                            pdf_text = self._extract_pdf_text(response.content)
                        elif 'text/html' in content_type:
                            pdf_text = self._extract_html_text(response.content)
                        else:
                            continue

                        if pdf_text:
                            extracted = self._extract_indicators_from_text(
                                pdf_text,
                                company_id,
                                f'esg_study_{self.year}_{i}',
                                'ESG Study'
                            )
                            indicators_found += extracted
                            print(f"       SUCCESS: {extracted} ESG study indicators")

                except Exception as e:
                    print(f"       ERROR: {str(e)[:50]}...")
                    continue

                time.sleep(2)

            print(f"   ESG STUDIES TOTAL: {indicators_found} indicators")
            return indicators_found

        except Exception as e:
            print(f"   ESG studies error: {str(e)[:50]}...")
            return 0

    def _download_investor_presentations(self, company_id: int):
        """Download and extract data from investor presentations"""
        print(f"\n5. DOWNLOADING INVESTOR PRESENTATIONS...")

        try:
            presentation_urls = self._search_investor_presentations()
            indicators_found = 0

            for i, url in enumerate(presentation_urls[:2], 1):
                print(f"   [{i}] Processing presentation: {url[:60]}...")

                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:

                        # Handle PDF presentations
                        if 'application/pdf' in response.headers.get('content-type', ''):
                            pdf_text = self._extract_pdf_text(response.content)
                            if pdf_text:
                                extracted = self._extract_indicators_from_text(
                                    pdf_text,
                                    company_id,
                                    f'presentation_{self.year}_{i}',
                                    'Investor Presentation'
                                )
                                indicators_found += extracted
                                print(f"       SUCCESS: {extracted} presentation indicators")

                except Exception as e:
                    print(f"       ERROR: {str(e)[:50]}...")
                    continue

                time.sleep(1)

            print(f"   INVESTOR PRESENTATIONS TOTAL: {indicators_found} indicators")
            return indicators_found

        except Exception as e:
            print(f"   Presentations error: {str(e)[:50]}...")
            return 0

    # ===========================================
    # DOCUMENT SEARCH METHODS
    # ===========================================

    def _search_annual_reports(self):
        """Search for annual reports online"""
        search_queries = [
            f"{self.company_name} annual report {self.year} filetype:pdf",
            f"{self.company_name} annual report {self.year} site:bseindia.com",
            f"{self.company_name} annual report {self.year} site:nseindia.com",
            f"{self.company_name} {self.year} annual report investor relations"
        ]

        return self._search_documents(search_queries)

    def _search_brsr_reports(self):
        """Search for BRSR reports online"""
        search_queries = [
            f"{self.company_name} BRSR report {self.year} filetype:pdf",
            f"{self.company_name} business responsibility sustainability report {self.year}",
            f"{self.company_name} BRSR {self.year} site:bseindia.com",
            f"{self.company_name} sustainability reporting {self.year}"
        ]

        return self._search_documents(search_queries)

    def _search_sustainability_reports(self):
        """Search for sustainability reports online"""
        search_queries = [
            f"{self.company_name} sustainability report {self.year} filetype:pdf",
            f"{self.company_name} ESG report {self.year}",
            f"{self.company_name} environmental report {self.year}",
            f"{self.company_name} corporate responsibility {self.year}"
        ]

        return self._search_documents(search_queries)

    def _search_esg_studies(self):
        """Search for ESG studies and research"""
        search_queries = [
            f"{self.company_name} ESG analysis {self.year}",
            f"{self.company_name} environmental social governance {self.year}",
            f"{self.company_name} ESG rating report {self.year}",
            f"{self.company_name} sustainability study {self.year}"
        ]

        return self._search_documents(search_queries)

    def _search_investor_presentations(self):
        """Search for investor presentations"""
        search_queries = [
            f"{self.company_name} investor presentation {self.year} filetype:pdf",
            f"{self.company_name} earnings presentation {self.year}",
            f"{self.company_name} quarterly results {self.year}",
            f"{self.company_name} analyst presentation {self.year}"
        ]

        return self._search_documents(search_queries)

    def _search_documents(self, search_queries):
        """Generic document search using multiple queries"""
        found_urls = set()

        for query in search_queries[:2]:  # Limit queries to avoid rate limits
            try:
                search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
                response = self.session.get(search_url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract PDF links from search results
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if any(ext in href.lower() for ext in ['.pdf', 'annual', 'report', 'brsr', 'sustainability']):
                            if href.startswith('http'):
                                found_urls.add(href)
                            elif href.startswith('/url?q='):
                                # Extract actual URL from Bing redirect
                                actual_url = href.split('/url?q=')[1].split('&')[0]
                                if actual_url.startswith('http'):
                                    found_urls.add(actual_url)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"   Search error for '{query[:50]}...': {str(e)[:30]}...")
                continue

        return list(found_urls)

    # ===========================================
    # TEXT EXTRACTION METHODS
    # ===========================================

    def _extract_pdf_text(self, pdf_content):
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            # Extract text from first 50 pages (most reports have key data early)
            for page_num in range(min(50, len(pdf_reader.pages))):
                try:
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                except Exception:
                    continue

            return text if len(text) > 100 else None

        except Exception:
            return None

    def _extract_html_text(self, html_content):
        """Extract text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text if len(text) > 100 else None

        except Exception:
            return None

    # ===========================================
    # INDICATOR EXTRACTION METHODS
    # ===========================================

    def _extract_indicators_from_text(self, text: str, company_id: int, source_name: str, document_type: str):
        """Extract ESG indicator values from document text using comprehensive patterns"""

        indicators_found = 0
        db = get_session()

        try:
            # Define comprehensive indicator patterns
            indicator_patterns = {
                # Financial Indicators
                'IMP-M03-I01': [  # Revenue
                    r'revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*crore',
                    r'total revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'net revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'revenue.*?(?:rs|inr|₹)\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
                ],
                'IMP-M03-I02': [  # Net Profit
                    r'net profit.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*crore',
                    r'profit after tax.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'net income.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'pat.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*crore'
                ],

                # Employee Indicators
                'IMP-M15-I01': [  # Total Employees
                    r'total employees.*?(\d{1,3}(?:,\d{3})*)',
                    r'workforce.*?(\d{1,3}(?:,\d{3})*)',
                    r'employee strength.*?(\d{1,3}(?:,\d{3})*)',
                    r'permanent employees.*?(\d{1,3}(?:,\d{3})*)'
                ],
                'IMP-M15-I02': [  # Women Employees
                    r'women employees.*?(\d{1,3}(?:,\d{3})*)',
                    r'female employees.*?(\d{1,3}(?:,\d{3})*)',
                    r'women.*?workforce.*?(\d{1,3}(?:,\d{3})*)',
                    r'gender diversity.*?(\d+\.?\d*)%'
                ],

                # Environmental Indicators
                'IMP-M05-I01': [  # GHG Emissions Scope 1
                    r'scope 1.*?emissions.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'direct emissions.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'scope 1.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*tco2',
                    r'ghg scope 1.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
                ],
                'IMP-M05-I02': [  # GHG Emissions Scope 2
                    r'scope 2.*?emissions.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'indirect emissions.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'scope 2.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*tco2',
                    r'purchased electricity.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
                ],
                'IMP-M06-I01': [  # Energy Consumption
                    r'total energy consumption.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'energy consumed.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'energy usage.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*mwh',
                    r'electricity consumption.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
                ],
                'IMP-M07-I01': [  # Water Consumption
                    r'water consumption.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'water usage.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'water withdrawal.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'total water.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kl'
                ],
                'IMP-M08-I01': [  # Waste Generated
                    r'waste generated.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'total waste.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'waste production.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'hazardous waste.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*mt'
                ],

                # Governance Indicators
                'IMP-M01-I01': [  # CIN Number
                    r'cin.*?([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})',
                    r'corporate identification number.*?([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})',
                    r'company registration.*?([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})'
                ],

                # Safety Indicators
                'IMP-M12-I01': [  # Safety Incidents
                    r'safety incidents.*?(\d+)',
                    r'workplace accidents.*?(\d+)',
                    r'injury rate.*?(\d+\.?\d*)',
                    r'lost time injury.*?(\d+)'
                ],

                # Training Indicators
                'IMP-M13-I01': [  # Training Hours
                    r'training hours.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'learning hours.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'development hours.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                    r'training.*?per employee.*?(\d+\.?\d*)\s*hours'
                ]
            }

            # Process text to find indicator values
            text_lower = text.lower()

            for indicator_id, patterns in indicator_patterns.items():
                for pattern in patterns:
                    try:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
                        if matches:
                            # Take the first valid match
                            value = matches[0]
                            if value and len(str(value)) > 0:

                                # Store the indicator
                                scraped_data = ScrapedData(
                                    company_id=company_id,
                                    year=self.year,
                                    source=source_name,
                                    data_key=indicator_id,
                                    data_value=f"{value} (from {document_type})",
                                    metadata={
                                        'extraction_method': 'regex_pattern',
                                        'document_type': document_type,
                                        'pattern_used': pattern,
                                        'confidence': 0.90
                                    }
                                )
                                db.add(scraped_data)
                                indicators_found += 1
                                print(f"       FOUND {indicator_id}: {value} (from {document_type})")
                                break  # Move to next indicator after finding first match
                    except Exception:
                        continue

            if indicators_found > 0:
                db.commit()

            return indicators_found

        except Exception as e:
            print(f"       Extraction error: {str(e)[:50]}...")
            db.rollback()
            return 0
        finally:
            db.close()


def enhance_dynamic_pattern_sources_with_documents(company_id: int, company_name: str, year: int):
    """Enhanced dynamic pattern sources with comprehensive document scraping"""

    print(f"=" * 100)
    print(f"ENHANCED DYNAMIC PATTERN SOURCES WITH COMPREHENSIVE DOCUMENTS")
    print(f"Company: {company_name} | Year: {year}")
    print(f"Sources: Web Patterns + Annual Reports + BRSR + Sustainability + ESG Studies")
    print(f"=" * 100)

    total_indicators = 0

    # 1. Run existing dynamic pattern sources (web scraping)
    try:
        from dynamic_pattern_sources import run_dynamic_pattern_extraction
        pattern_indicators = run_dynamic_pattern_extraction(company_id, company_name, year)
        total_indicators += pattern_indicators
        print(f"\nExisting pattern sources: {pattern_indicators} indicators")
    except Exception as e:
        print(f"Pattern sources error: {str(e)[:50]}...")
        pattern_indicators = 0

    # 2. Run comprehensive document scraping
    try:
        scraper = ComprehensiveDocumentScraper(company_name, year)
        document_indicators = scraper.download_and_scrape_all_documents(company_id)
        total_indicators += document_indicators
        print(f"\nDocument scraping: {document_indicators} indicators")
    except Exception as e:
        print(f"Document scraping error: {str(e)[:50]}...")
        document_indicators = 0

    print(f"\n" + "=" * 100)
    print(f"ENHANCED DYNAMIC PATTERN SOURCES COMPLETE")
    print(f"Total indicators from ALL sources: {total_indicators}")
    print(f"Breakdown:")
    print(f"  • Web pattern sources: {pattern_indicators} indicators")
    print(f"  • Document sources: {document_indicators} indicators")
    print(f"Coverage improvement: From basic patterns to comprehensive document extraction")
    print(f"=" * 100)

    return total_indicators


if __name__ == "__main__":
    # Test with Bank of Baroda (the company from the user's log that had low coverage)
    test_company_name = "BANK OF BARODA"
    test_company_id = 26  # From the log
    test_year = 2024

    print("Testing enhanced dynamic pattern sources with comprehensive document scraping...")
    result = enhance_dynamic_pattern_sources_with_documents(test_company_id, test_company_name, test_year)
    print(f"\nTEST RESULT: {result} total indicators extracted from ALL sources!")