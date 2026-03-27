#!/usr/bin/env python3
"""
ONLINE ESG DATA SCRAPER
Scrapes missing ESG indicators from online sources
Sources: Company websites, BSE/NSE, Screener.in, Money Control, etc.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import requests
import re
from typing import Dict, List, Optional
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

class OnlineESGScraper:
    """Scrape missing ESG data from online sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_from_screener(self, company_name: str, symbol: str) -> Dict[str, str]:
        """Scrape financial data from Screener.in"""

        data = {}

        try:
            # Try to find company on Screener
            search_url = f"https://www.screener.in/api/company/search/?q={symbol}"

            print(f"  Searching Screener.in for: {symbol}")
            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200:
                results = response.json()
                if results:
                    # Get first result
                    company_id = results[0].get('id')
                    # Use the URL from API response instead
                    company_url = f"https://www.screener.in{results[0].get('url')}"

                    print(f"    Found company URL: {company_url}")

                    # Fetch company page
                    page_response = self.session.get(company_url, timeout=10)
                    if page_response.status_code == 200:
                        html = page_response.text

                        # Extract financial metrics using Screener.in structure
                        # Market Cap - from summary section
                        market_cap_match = re.search(r'Market Cap.*?<span class="number">([0-9,]+)</span>', html, re.DOTALL)
                        if market_cap_match:
                            data['IMP-M03-I05'] = f"{market_cap_match.group(1)} Cr"
                            print(f"    FOUND IMP-M03-I05 (Market Cap): {data['IMP-M03-I05']}")

                        # Current Stock Price
                        price_match = re.search(r'Current Price.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>', html, re.DOTALL)
                        if price_match:
                            data['IMP-M03-I06'] = f"Rs {price_match.group(1)}"
                            print(f"    FOUND IMP-M03-I06 (Stock Price): {data['IMP-M03-I06']}")

                        # ROE (Return on Equity)
                        roe_match = re.search(r'ROE.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>', html, re.DOTALL)
                        if roe_match:
                            data['IMP-M16-I02'] = f"{roe_match.group(1)}%"
                            print(f"    FOUND IMP-M16-I02 (ROE): {data['IMP-M16-I02']}")

                        # ROCE (Return on Capital Employed)
                        roce_match = re.search(r'ROCE.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>', html, re.DOTALL)
                        if roce_match:
                            data['IMP-M16-I03'] = f"{roce_match.group(1)}%"
                            print(f"    FOUND IMP-M16-I03 (ROCE): {data['IMP-M16-I03']}")

                        # Book Value
                        bv_match = re.search(r'Book Value.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>', html, re.DOTALL)
                        if bv_match:
                            data['IMP-M16-I04'] = f"Rs {bv_match.group(1)}"
                            print(f"    FOUND IMP-M16-I04 (Book Value): {data['IMP-M16-I04']}")

                        # Dividend Yield
                        div_match = re.search(r'Dividend Yield.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>', html, re.DOTALL)
                        if div_match:
                            data['IMP-M16-I05'] = f"{div_match.group(1)}%"
                            print(f"    FOUND IMP-M16-I05 (Dividend Yield): {data['IMP-M16-I05']}")

                        print(f"    Extracted {len(data)} indicators from Screener.in")

        except Exception as e:
            print(f"    Screener.in error: {str(e)}")

        return data

    def scrape_from_bse(self, symbol: str) -> Dict[str, str]:
        """Scrape data from BSE India"""

        data = {}

        try:
            print(f"  Checking BSE India for: {symbol}")

            # BSE company search
            bse_url = f"https://www.bseindia.com/stock-share-price/results.aspx?scripcode={symbol}&Submit=Submit"

            response = self.session.get(bse_url, timeout=10)
            if response.status_code == 200:
                html = response.text

                # Extract company info
                company_name_match = re.search(r'<span[^>]*id="lblCompanyName"[^>]*>([^<]+)</span>', html)
                if company_name_match:
                    data['IMP-M01-I01'] = company_name_match.group(1).strip()
                    print(f"    FOUND IMP-M01-I01 (Company Name): {data['IMP-M01-I01']}")

                # Market cap
                mcap_match = re.search(r'Market Cap[:\s]*(?:Rs\.?)?\s*([0-9,\.]+)\s*Cr', html, re.IGNORECASE)
                if mcap_match:
                    data['IMP-M03-I05'] = f"{mcap_match.group(1)} Cr"
                    print(f"    FOUND IMP-M03-I05 (Market Cap): {data['IMP-M03-I05']}")

                print(f"    Extracted {len(data)} indicators from BSE")

        except Exception as e:
            print(f"    BSE error: {str(e)}")

        return data

    def scrape_from_company_website(self, website: str) -> Dict[str, str]:
        """Scrape from company's official website"""

        data = {}

        if not website:
            return data

        try:
            print(f"  Checking company website: {website}")

            # Try common investor relations pages
            ir_pages = [
                f"{website}/investors",
                f"{website}/investor-relations",
                f"{website}/investors/financial-information",
                f"{website}/sustainability",
                f"{website}/esg"
            ]

            for page_url in ir_pages:
                try:
                    response = self.session.get(page_url, timeout=10)
                    if response.status_code == 200:
                        html = response.text

                        # Look for sustainability/ESG mentions
                        if 'sustainability' in html.lower() or 'esg' in html.lower():
                            data['IMP-M02-I01'] =f"Sustainability information available at {page_url}"
                            print(f"    FOUND sustainability page: {page_url}")
                            break

                except:
                    continue

        except Exception as e:
            print(f"    Website error: {str(e)}")

        return data

    def scrape_missing_indicators(self, company_id: int, year: int, missing_indicators: List[str]) -> Dict[str, str]:
        """Scrape missing indicators from all online sources"""

        db = get_session()
        all_data = {}

        try:
            company = db.query(Company).filter_by(id=company_id).first()
            if not company:
                return all_data

            print(f"\nONLINE DATA SCRAPING FOR MISSING INDICATORS")
            print(f"Company: {company.name}")
            print(f"Missing: {len(missing_indicators)} indicators")
            print("=" * 60)

            # Source 1: Screener.in (financial data)
            if company.ticker:
                screener_data = self.scrape_from_screener(company.name, company.ticker)
                all_data.update(screener_data)

            # Source 2: BSE India
            if company.ticker:
                bse_data = self.scrape_from_bse(company.ticker)
                all_data.update(bse_data)

            # Source 3: Company website
            if company.website:
                website_data = self.scrape_from_company_website(company.website)
                all_data.update(website_data)

            print(f"\n" + "="*60)
            print(f"ONLINE SCRAPING COMPLETE:")
            print(f"  Total indicators found online: {len(all_data)}")
            print(f"  Remaining missing: {len(missing_indicators) - len(all_data)}")
            print("="*60)

            return all_data

        finally:
            db.close()

def scrape_and_store_missing_data(company_id: int, year: int):
    """Main function: identify missing indicators and scrape from online"""

    db = get_session()

    try:
        # Get what's already extracted from PDFs
        existing_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        existing_indicators = {data.data_key for data in existing_data}

        # All 151 indicators (simplified list for modules we have patterns for)
        all_indicators = [f"IMP-M{m:02d}-I{i:02d}" for m in range(1, 22) for i in range(1, 16)]
        all_indicators = all_indicators[:151]  # Limit to 151

        missing_indicators = [ind for ind in all_indicators if ind not in existing_indicators]

        print(f"MISSING INDICATOR ANALYSIS:")
        print(f"  Total indicators: 151")
        print(f"  Already extracted: {len(existing_indicators)}")
        print(f"  Missing: {len(missing_indicators)}")
        print()

        if not missing_indicators:
            print("All indicators already extracted!")
            return 0

        # Scrape missing indicators from online
        scraper = OnlineESGScraper()
        online_data = scraper.scrape_missing_indicators(company_id, year, missing_indicators)

        # Store online data
        if online_data:
            stored_count = 0
            for indicator_id, value in online_data.items():
                existing = db.query(ScrapedData).filter_by(
                    company_id=company_id,
                    year=year,
                    source='online_scraping',
                    data_key=indicator_id
                ).first()

                if existing:
                    existing.data_value = value
                else:
                    scraped_data = ScrapedData(
                        company_id=company_id,
                        year=year,
                        source='online_scraping',
                        data_key=indicator_id,
                        data_value=value
                    )
                    db.add(scraped_data)

                stored_count += 1

            db.commit()
            print(f"\nSTORED {stored_count} indicators from online sources")
            return stored_count

        return 0

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC Limited
    company_id = 30
    result = scrape_and_store_missing_data(company_id, 2024)
    print(f"\nFINAL: {result} indicators scraped from online sources")