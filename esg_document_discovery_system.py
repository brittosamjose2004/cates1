#!/usr/bin/env python3
"""
Comprehensive ESG Document Discovery & Extraction System
Uses Hugging Face Web Search to find, download and extract ESG documents

Features:
1. Web search for ESG documents (annual reports, BRSR, sustainability reports)
2. Automatic document download from discovered URLs
3. PDF/document extraction and analysis
4. Integration with existing ESG pipeline

Author: Claude
Date: March 26, 2026
"""

import sys
import os
import requests
import time
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import ScrapedData, Company


class ESGDocumentDiscoverySystem:
    """
    Complete ESG document discovery and extraction system
    Uses Hugging Face web search + automatic document processing
    """

    def __init__(self):
        project_root = Path(__file__).resolve().parent
        # Prefer external scraper workspace if available, else local annual_reports cache.
        external_workspace = project_root / "scrapper_new-main"
        external_root = external_workspace / "downloads" / "nseindia.com"
        self.base_download_dir = external_root if external_workspace.exists() else (project_root / "data" / "annual_reports")
        self.base_download_dir.mkdir(parents=True, exist_ok=True)

        self.external_download_roots = [
            external_workspace / "downloads" / "nseindia.com",
            external_workspace / "downloads" / "annualreports.com",
        ]

        # Initialize Gradio client for web search
        try:
            from gradio_client import Client
            self.search_client = Client("https://victor-websearch.hf.space/")
            self.web_search_available = True
            print("* Hugging Face Web Search client initialized")
        except Exception as e:
            print(f"* Warning: Gradio client failed to initialize: {e}")
            self.web_search_available = False

        # Document type patterns
        self.document_patterns = {
            'annual_report': [
                'annual report', 'annual disclosure', 'yearly report',
                'annual statement', 'comprehensive report'
            ],
            'sustainability_report': [
                'sustainability report', 'esg report', 'responsibility report',
                'impact report', 'environmental report', 'csr report'
            ],
            'brsr_report': [
                'brsr report', 'business responsibility', 'sustainability reporting',
                'brsr disclosure', 'national guidelines'
            ],
            'integrated_report': [
                'integrated report', 'integrated annual report',
                'value creation report', 'ir report'
            ]
        }

        # File extensions to download
        self.downloadable_extensions = {'.pdf', '.doc', '.docx', '.xlsx', '.xls'}

    def _company_year_download_dir(self, company_name: str, year: int) -> Path:
        """Return deterministic download folder by company and year."""
        company_clean = re.sub(r'[^\w\s-]', '', company_name or "company")
        company_clean = re.sub(r'[-\s]+', '_', company_clean).strip('_') or "company"
        out_dir = self.base_download_dir / company_clean / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def discover_company_esg_documents(self, company_name: str, year: int) -> List[Dict[str, Any]]:
        """
        Complete ESG document discovery for a company

        Returns:
            List of discovered document information with download results
        """

        print(f"=== ESG DOCUMENT DISCOVERY: {company_name} ({year}) ===")

        if not self.web_search_available:
            print("* Web search not available, skipping document discovery")
            return []

        discovered_documents = []
        downloaded_docs = []

        # Phase -1: ingest reports already present in scrapper_new-main downloads
        external_docs = self._load_external_scraper_documents(company_name, year)
        if external_docs:
            print(f"* Found {len(external_docs)} reports in scrapper_new-main downloads")
            downloaded_docs.extend(external_docs)

        # Phase 0: Use local annual-report folder first (company/year cache)
        local_docs = self._load_existing_local_documents(company_name, year)
        if local_docs:
            print(f"* Found {len(local_docs)} existing local documents in annual-reports folder")
            downloaded_docs.extend(local_docs)

        # Phase 1: Search for each document type
        for doc_type, search_terms in self.document_patterns.items():
            print(f"* Searching for {doc_type}...")

            docs_found = self._search_document_type(company_name, year, doc_type, search_terms)
            discovered_documents.extend(docs_found)

            # Rate limiting
            time.sleep(1)

        # Phase 2: Download discovered documents
        print(f"* Found {len(discovered_documents)} potential documents")

        for doc_info in discovered_documents:
            download_result = self._download_document(doc_info)
            if download_result:
                downloaded_docs.append(download_result)

        print(f"* Successfully downloaded {len(downloaded_docs)} documents")

        # Phase 3: Extract data from downloaded documents
        extracted_data = []
        for doc_info in downloaded_docs:
            extraction_results = self._extract_document_data(doc_info, company_name, year)
            extracted_data.extend(extraction_results)

        print(f"* Extracted {len(extracted_data)} ESG indicators from documents")

        return extracted_data

    def _load_existing_local_documents(self, company_name: str, year: int) -> List[Dict[str, Any]]:
        """Load already-downloaded company/year documents from local annual-reports folder."""
        local_dir = self._company_year_download_dir(company_name, year)
        docs: List[Dict[str, Any]] = []

        try:
            for path in local_dir.glob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in self.downloadable_extensions:
                    continue

                doc_type = "annual_report"
                lower_name = path.name.lower()
                if "sustainability" in lower_name or "esg" in lower_name:
                    doc_type = "sustainability_report"
                elif "brsr" in lower_name or "business_responsibility" in lower_name:
                    doc_type = "brsr_report"
                elif "integrated" in lower_name or "value_creation" in lower_name:
                    doc_type = "integrated_report"

                docs.append({
                    'url': f'file://{path.name}',
                    'document_type': doc_type,
                    'company_name': company_name,
                    'year': year,
                    'discovered_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'source': 'local_annual_reports_folder',
                    'filepath': str(path),
                    'download_status': 'already_exists',
                    'file_size': path.stat().st_size,
                })
        except Exception as e:
            print(f"* Warning: Could not load existing local documents: {e}")

        return docs

    def _normalize_company_token(self, name: str) -> str:
        cleaned = re.sub(r'[^\w\s-]', '', name or "")
        return re.sub(r'[-\s]+', '_', cleaned).strip('_').lower()

    def _load_external_scraper_documents(self, company_name: str, year: int) -> List[Dict[str, Any]]:
        """Load reports from scrapper_new-main/downloads by company match and year."""
        docs: List[Dict[str, Any]] = []
        target_token = self._normalize_company_token(company_name)
        year_str = str(year)

        for root in self.external_download_roots:
            if not root.exists():
                continue

            try:
                # scraper_new-main stores company folders under source roots.
                for company_dir in root.iterdir():
                    if not company_dir.is_dir():
                        continue

                    folder_token = self._normalize_company_token(company_dir.name)
                    if not folder_token:
                        continue

                    if target_token not in folder_token and folder_token not in target_token:
                        continue

                    for path in company_dir.rglob("*.pdf"):
                        pstr = str(path).lower()
                        if year_str not in pstr:
                            continue

                        lower_name = path.name.lower()
                        doc_type = "annual_report"
                        if "sustainability" in lower_name or "esg" in lower_name:
                            doc_type = "sustainability_report"
                        elif "brsr" in lower_name or "business_responsibility" in lower_name:
                            doc_type = "brsr_report"
                        elif "integrated" in lower_name or "value_creation" in lower_name:
                            doc_type = "integrated_report"

                        docs.append({
                            'url': f'file://{path.name}',
                            'document_type': doc_type,
                            'company_name': company_name,
                            'year': year,
                            'discovered_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'source': 'scrapper_new_main_folder',
                            'filepath': str(path),
                            'download_status': 'already_exists',
                            'file_size': path.stat().st_size,
                        })
            except Exception as e:
                print(f"* Warning: Could not read external scraper folder {root}: {e}")

        # Deduplicate by filepath
        unique: Dict[str, Dict[str, Any]] = {}
        for doc in docs:
            unique[doc['filepath']] = doc
        return list(unique.values())

    def _search_document_type(self, company_name: str, year: int, doc_type: str, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search for specific document type using web search"""

        documents_found = []

        for term in search_terms:
            # Construct search query
            search_queries = [
                f'"{company_name}" {term} {year} filetype:pdf',
                f'"{company_name}" {term} {year}',
                f'{company_name} {term} {year} annual',
                f'{company_name} {term} {year-1}-{year}',  # Financial year format
            ]

            for query in search_queries:
                try:
                    print(f"  Query: {query}")

                    # Call Hugging Face Web Search
                    search_result = self.search_client.predict(
                        query,  # Just pass the query directly
                        "general",  # search_type
                        5  # num_results
                    )

                    # Parse search results
                    parsed_docs = self._parse_search_results(search_result, doc_type, company_name, year)
                    documents_found.extend(parsed_docs)

                    # Rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    print(f"    Search failed for '{query}': {str(e)}")
                    continue

        # Remove duplicates
        unique_documents = self._remove_duplicate_documents(documents_found)

        print(f"  Found {len(unique_documents)} unique {doc_type} documents")
        return unique_documents

    def _parse_search_results(self, search_result: Any, doc_type: str, company_name: str, year: int) -> List[Dict[str, Any]]:
        """Parse search results to extract document URLs"""

        documents = []

        try:
            # Handle different result formats from Gradio
            if isinstance(search_result, str):
                content = search_result
            elif isinstance(search_result, list) and len(search_result) > 0:
                content = search_result[0] if isinstance(search_result[0], str) else str(search_result)
            else:
                content = str(search_result)

            # Extract URLs from content using regex
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.pdf|\.doc|\.docx|\.xlsx|\.xls|/[^\s]*)'
            urls_found = re.findall(url_pattern, content)

            # Also look for domain-based URLs (annual report sections)
            domain_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:annual|sustainability|esg|report|investor)[^\s]*'
            domain_urls = re.findall(domain_pattern, content)
            urls_found.extend(domain_urls)

            for url in urls_found:
                # Clean URL
                clean_url = url.strip('",.:;')

                # Validate URL
                if self._is_valid_document_url(clean_url, doc_type):
                    documents.append({
                        'url': clean_url,
                        'document_type': doc_type,
                        'company_name': company_name,
                        'year': year,
                        'discovered_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'source': 'huggingface_websearch',
                        'content_snippet': content[:200] + "..." if len(content) > 200 else content
                    })

        except Exception as e:
            print(f"    Error parsing search results: {str(e)}")

        return documents

    def _is_valid_document_url(self, url: str, doc_type: str) -> bool:
        """Validate if URL is likely to contain ESG documents"""

        try:
            parsed_url = urlparse(url)

            # Check domain quality (not social media, not search engines)
            invalid_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'google.com', 'bing.com']
            if any(domain in parsed_url.netloc.lower() for domain in invalid_domains):
                return False

            # Check path keywords
            path_lower = parsed_url.path.lower()

            # Strong indicators
            good_keywords = ['annual', 'sustainability', 'esg', 'report', 'investor', 'disclosure', 'brsr']
            if any(keyword in path_lower for keyword in good_keywords):
                return True

            # File extension check
            if any(path_lower.endswith(ext) for ext in self.downloadable_extensions):
                return True

            # Domain-specific checks (corporate websites)
            if any(indicator in parsed_url.netloc.lower() for indicator in ['.com', '.in', '.org']):
                return True

            return False

        except Exception:
            return False

    def _remove_duplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on URL"""

        seen_urls = set()
        unique_docs = []

        for doc in documents:
            url_hash = hashlib.md5(doc['url'].encode()).hexdigest()
            if url_hash not in seen_urls:
                seen_urls.add(url_hash)
                unique_docs.append(doc)

        return unique_docs

    def _download_document(self, doc_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Download document from URL"""

        try:
            url = doc_info['url']
            print(f"  Downloading: {url}")

            # Generate filename in company/year annual-report folder
            filename = self._generate_filename(doc_info)
            download_dir = self._company_year_download_dir(doc_info.get('company_name', ''), int(doc_info.get('year', 0) or 0))
            filepath = download_dir / filename

            # Check if already downloaded
            if filepath.exists():
                print(f"    Already downloaded: {filename}")
                doc_info['filepath'] = str(filepath)
                doc_info['download_status'] = 'already_exists'
                return doc_info

            # Download file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=45, stream=True, allow_redirects=True)
            response.raise_for_status()

            content_type = (response.headers.get('Content-Type') or '').lower()

            # Skip HTML pages masquerading as downloadable docs.
            if 'text/html' in content_type:
                print(f"    Skipping non-document content: {content_type}")
                return None

            # Save file
            first_bytes = b''
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        if len(first_bytes) < 8:
                            first_bytes += chunk[:8 - len(first_bytes)]
                        f.write(chunk)

            # Reject files that are too small or not likely valid documents
            size = filepath.stat().st_size
            is_pdf = filepath.suffix.lower() == '.pdf'
            pdf_signature_ok = first_bytes.startswith(b'%PDF')

            if is_pdf and not pdf_signature_ok:
                # Some servers lie about extension; reject invalid PDF bytes.
                print(f"    Invalid PDF signature, removing: {filename}")
                filepath.unlink(missing_ok=True)
                return None

            # Validate download
            if size > 1000:  # At least 1KB
                print(f"    Downloaded successfully: {filename} ({size} bytes)")
                doc_info['filepath'] = str(filepath)
                doc_info['download_status'] = 'success'
                doc_info['file_size'] = size
                return doc_info
            else:
                print(f"    Downloaded file too small, removing: {filename}")
                filepath.unlink(missing_ok=True)
                return None

        except requests.exceptions.RequestException as e:
            print(f"    Download failed: {str(e)}")
            return None
        except Exception as e:
            print(f"    Download error: {str(e)}")
            return None

    def _generate_filename(self, doc_info: Dict[str, Any]) -> str:
        """Generate filename for downloaded document"""

        # Clean company name
        company_clean = re.sub(r'[^\w\s-]', '', doc_info['company_name'])
        company_clean = re.sub(r'[-\s]+', '_', company_clean)

        # Hash URL to avoid collisions between multiple results of same document type
        url_hash = hashlib.md5((doc_info.get('url') or '').encode()).hexdigest()[:8]

        # Get file extension from URL
        url_path = urlparse(doc_info['url']).path
        extension = Path(url_path).suffix

        if not extension or extension.lower() not in ['.pdf', '.doc', '.docx', '.xlsx', '.xls']:
            extension = '.pdf'  # Default to PDF

        # Generate filename
        filename = f"{company_clean}_{doc_info['year']}_{doc_info['document_type']}_{url_hash}{extension}"

        return filename

    def _extract_document_data(self, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract ESG data from downloaded document"""

        try:
            filepath = doc_info['filepath']
            print(f"  Extracting data from: {Path(filepath).name}")

            # Use existing PDF extraction capabilities
            if filepath.lower().endswith('.pdf'):
                return self._extract_pdf_data(filepath, doc_info, company_name, year)
            elif filepath.lower().endswith(('.doc', '.docx')):
                return self._extract_word_data(filepath, doc_info, company_name, year)
            elif filepath.lower().endswith(('.xlsx', '.xls')):
                return self._extract_excel_data(filepath, doc_info, company_name, year)
            else:
                print(f"    Unsupported file type: {filepath}")
                return []

        except Exception as e:
            print(f"    Extraction failed: {str(e)}")
            return []

    def _extract_pdf_data(self, filepath: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract data from PDF document"""

        try:
            # Use existing PDF extraction infrastructure
            from backend.scraper.pdf_extractor import extract_text_from_pdf

            # Extract text from PDF
            pdf_text = extract_text_from_pdf(filepath)

            if not pdf_text or len(pdf_text.strip()) < 100:
                print(f"    PDF extraction failed or too little content")
                return []

            # Extract ESG indicators from text
            indicators = self._extract_esg_indicators_from_text(
                pdf_text, doc_info, company_name, year
            )

            print(f"    Extracted {len(indicators)} indicators from PDF")
            return indicators

        except ImportError:
            print(f"    PDF extraction not available, trying alternative method")
            return self._basic_pdf_extraction(filepath, doc_info, company_name, year)
        except Exception as e:
            print(f"    PDF extraction failed: {str(e)}")
            return []

    def _basic_pdf_extraction(self, filepath: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Basic PDF extraction using PyPDF2 or similar"""

        try:
            import PyPDF2

            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                # Extract text from first 20 pages (avoid huge documents)
                for page_num in range(min(20, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()

                if len(text.strip()) > 100:
                    indicators = self._extract_esg_indicators_from_text(
                        text, doc_info, company_name, year
                    )
                    return indicators

        except ImportError:
            print(f"    PyPDF2 not available for PDF extraction")
        except Exception as e:
            print(f"    Basic PDF extraction failed: {str(e)}")

        return []

    def _extract_word_data(self, filepath: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract data from Word document"""

        try:
            import docx

            doc = docx.Document(filepath)
            text = ""

            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

            if len(text.strip()) > 100:
                indicators = self._extract_esg_indicators_from_text(
                    text, doc_info, company_name, year
                )
                return indicators

        except ImportError:
            print(f"    python-docx not available for Word extraction")
        except Exception as e:
            print(f"    Word extraction failed: {str(e)}")

        return []

    def _extract_excel_data(self, filepath: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract data from Excel document"""

        try:
            import pandas as pd

            # Read all sheets
            excel_file = pd.ExcelFile(filepath)
            combined_text = ""

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                combined_text += df.to_string() + "\n\n"

            if len(combined_text.strip()) > 100:
                indicators = self._extract_esg_indicators_from_text(
                    combined_text, doc_info, company_name, year
                )
                return indicators

        except ImportError:
            print(f"    pandas not available for Excel extraction")
        except Exception as e:
            print(f"    Excel extraction failed: {str(e)}")

        return []

    def _extract_esg_indicators_from_text(self, text: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
        """Extract ESG indicators from document text"""

        indicators = []
        text_lower = text.lower()

        # Enhanced ESG patterns for document extraction
        esg_patterns = {
            # Environmental indicators
            'IMP-M05-I01': [
                'carbon emission', 'co2 emission', 'greenhouse gas', 'ghg emission',
                'carbon footprint', 'emission reduction', 'scope 1', 'scope 2', 'scope 3'
            ],
            'IMP-M05-I02': [
                'energy consumption', 'renewable energy', 'energy usage', 'power consumption',
                'energy efficiency', 'clean energy', 'solar', 'wind energy'
            ],
            'IMP-M06-I01': [
                'water consumption', 'water usage', 'water withdrawal', 'water intensity',
                'water management', 'water conservation'
            ],
            'IMP-M07-I01': [
                'waste generation', 'waste disposal', 'recycling', 'waste management',
                'circular economy', 'zero waste'
            ],

            # Social indicators
            'IMP-M15-I01': [
                'number of employees', 'workforce', 'staff strength', 'employee count',
                'total employees', 'human resources'
            ],
            'IMP-M15-I02': [
                'diversity', 'gender equality', 'women employees', 'inclusion',
                'diversity ratio', 'female participation'
            ],
            'IMP-M14-I01': [
                'workplace safety', 'occupational health', 'safety performance',
                'accident rate', 'safety training', 'safety measures'
            ],
            'IMP-M16-I01': [
                'csr spending', 'csr expenditure', 'social contribution', 'community investment',
                'social responsibility', 'csr activities'
            ],

            # Governance indicators
            'IMP-M01-I01': [
                'business profile', 'company overview', 'business description',
                'nature of business', 'business activities'
            ],
            'IMP-M03-I01': [
                'total revenue', 'revenue', 'net sales', 'turnover',
                'total income', 'gross revenue'
            ],
            'IMP-M03-I02': [
                'board composition', 'board of directors', 'independent directors',
                'board diversity', 'governance structure'
            ],
            'IMP-M04-I01': [
                'risk management', 'risk assessment', 'risk framework',
                'compliance', 'regulatory compliance', 'risk mitigation'
            ]
        }

        for indicator_id, keywords in esg_patterns.items():
            best_match = None
            best_confidence = 0

            for keyword in keywords:
                if keyword in text_lower:
                    # Extract context around the keyword
                    start_idx = text_lower.find(keyword)
                    context_start = max(0, start_idx - 150)
                    context_end = min(len(text), start_idx + len(keyword) + 150)
                    context = text[context_start:context_end].strip()

                    # Calculate confidence based on document type and keyword match
                    confidence = self._calculate_extraction_confidence(
                        doc_info['document_type'], keyword, context
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = context

            if best_match and best_confidence > 0.6:  # Minimum confidence threshold
                indicators.append({
                    'indicator_id': indicator_id,
                    'data_value': f"[{doc_info['document_type'].title()}] {best_match}",
                    'source': f"discovered_document_{doc_info['document_type']}_{doc_info['source']}",
                    'confidence': best_confidence,
                    'document_url': doc_info['url'],
                    'document_type': doc_info['document_type'],
                    'extraction_method': 'document_text_analysis',
                    'company_name': company_name,
                    'year': year
                })

        return indicators

    def _calculate_extraction_confidence(self, doc_type: str, keyword: str, context: str) -> float:
        """Calculate confidence for extracted data"""

        base_confidence = {
            'annual_report': 0.90,
            'sustainability_report': 0.95,
            'brsr_report': 0.95,
            'integrated_report': 0.85
        }.get(doc_type, 0.70)

        # Boost confidence if context contains numbers or specific terms
        context_lower = context.lower()

        # Look for numerical data
        import re
        if re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', context):
            base_confidence += 0.10

        # Look for units
        units = ['tons', 'tonnes', 'kwh', 'mwh', 'liters', 'gallons', 'percent', '%', 'crore', 'million']
        if any(unit in context_lower for unit in units):
            base_confidence += 0.05

        # Look for year references
        if any(str(year) in context for year in range(2020, 2030)):
            base_confidence += 0.05

        return min(base_confidence, 1.0)


def test_document_discovery_system():
    """Test the complete document discovery system"""

    print("=== TESTING ESG DOCUMENT DISCOVERY SYSTEM ===")

    try:
        # Initialize system
        discovery_system = ESGDocumentDiscoverySystem()

        if not discovery_system.web_search_available:
            print("* Web search not available, skipping test")
            return False

        # Test with Asian Paints
        print(f"Testing with Asian Paints...")

        discovered_data = discovery_system.discover_company_esg_documents("Asian Paints", 2024)

        print(f"* Discovery completed: {len(discovered_data)} ESG indicators extracted")

        if discovered_data:
            # Show sample results
            print(f"\\nSample discovered indicators:")
            for i, indicator in enumerate(discovered_data[:5]):
                print(f"  {i+1}. {indicator['indicator_id']}: {indicator['data_value'][:100]}...")
                print(f"     Source: {indicator['source']} (Confidence: {indicator['confidence']:.2f})")
                print(f"     Document: {indicator['document_type']} from {indicator['document_url']}")
                print()

            # Save to database (optional)
            save_to_db = input("Save discovered indicators to database? (y/n): ").lower() == 'y'

            if save_to_db:
                db = get_session()
                saved_count = 0

                for indicator in discovered_data:
                    try:
                        scraped_data = ScrapedData(
                            company_id=14,  # Asian Paints
                            year=2024,
                            data_key=indicator['indicator_id'],
                            data_value=indicator['data_value'],
                            source=indicator['source'],
                            confidence=indicator['confidence']
                        )
                        db.add(scraped_data)
                        saved_count += 1
                    except Exception as e:
                        print(f"    Failed to save {indicator['indicator_id']}: {str(e)}")

                try:
                    db.commit()
                    print(f"* Saved {saved_count} indicators to database")
                except Exception as e:
                    db.rollback()
                    print(f"* Database save failed: {str(e)}")
                finally:
                    db.close()

        return True

    except Exception as e:
        print(f"* Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test the complete system
    test_document_discovery_system()