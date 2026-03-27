#!/usr/bin/env python3
"""
COMPREHENSIVE ONLINE ESG SCRAPER
Scrapes from MULTIPLE online sources to fill all 151 ESG indicators
Sources: Screener.in, Money Control, BSE, NSE, Company Website, CSR databases
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import requests
import re
from typing import Dict, List
from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

class ComprehensiveOnlineScraper:
    """Scrapes ESG data from multiple online sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_all_sources(self, company: Company, missing_indicators: List[str]) -> Dict[str, str]:
        """Scrape from ALL available online sources"""

        all_data = {}

        print(f"\nSCRAPING FROM MULTIPLE SOURCES FOR: {company.name}")
        print("="*70)

        # SOURCE 1: Screener.in (Financial metrics)
        if company.ticker:
            screener_data = self.scrape_screener_in(company.name, company.ticker)
            all_data.update(screener_data)
            print(f"  Screener.in: {len(screener_data)} indicators")

        # SOURCE 2: Money Control (Comprehensive financial + ESG)
        if company.ticker:
            moneycontrol_data = self.scrape_money_control(company.ticker)
            all_data.update(moneycontrol_data)
            print(f"  Money Control: {len(moneycontrol_data)} indicators")

        # SOURCE 3: NSE India (Official exchange data)
        if company.ticker:
            nse_data = self.scrape_nse_india(company.ticker)
            all_data.update(nse_data)
            print(f"  NSE India: {len(nse_data)} indicators")

        # SOURCE 4: BSE India
        if company.ticker:
            bse_data = self.scrape_bse_india(company.ticker)
            all_data.update(bse_data)
            print(f"  BSE India: {len(bse_data)} indicators")

        # SOURCE 5: Company Website (Sustainability/ESG sections)
        if company.website:
            website_data = self.scrape_company_website(company.website)
            all_data.update(website_data)
            print(f"  Company Website: {len(website_data)} indicators")

        print(f"\nTOTAL INDICATORS FROM ONLINE: {len(all_data)}")

        return all_data

    def scrape_screener_in(self, company_name: str, ticker: str) -> Dict[str, str]:
        """Scrape from Screener.in"""
        data = {}

        try:
            # Search for company
            search_url = f'https://www.screener.in/api/company/search/?q={ticker}'
            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200:
                results = response.json()

                if results:
                    # Get company page
                    company_url = f"https://www.screener.in{results[0].get('url')}"
                    page_response = self.session.get(company_url, timeout=10)

                    if page_response.status_code == 200:
                        html = page_response.text

                        # Extract metrics using Screener.in structure
                        patterns = {
                            'IMP-M03-I05': r'Market Cap.*?<span class="number">([0-9,]+)</span>',
                            'IMP-M03-I06': r'Current Price.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M16-I02': r'ROE.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M16-I03': r'ROCE.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M16-I04': r'Book Value.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M16-I05': r'Dividend Yield.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M16-I06': r'Stock P/E.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                            'IMP-M03-I07': r'Face Value.*?<span class="number">([0-9,]+(?:\.[0-9]+)?)</span>',
                        }

                        for indicator_id, pattern in patterns.items():
                            match = re.search(pattern, html, re.DOTALL)
                            if match:
                                value = match.group(1)
                                # Add units
                                if indicator_id == 'IMP-M03-I05':
                                    data[indicator_id] = f"{value} Cr"
                                elif indicator_id == 'IMP-M03-I06':
                                    data[indicator_id] = f"Rs {value}"
                                elif 'I02' in indicator_id or 'I03' in indicator_id or 'I05' in indicator_id or 'I06' in indicator_id:
                                    data[indicator_id] = f"{value}%"
                                else:
                                    data[indicator_id] = f"Rs {value}"

        except Exception as e:
            print(f"    Screener.in error: {str(e)}")

        return data

    def scrape_money_control(self, ticker: str) -> Dict[str, str]:
        """Scrape from Money Control"""
        data = {}

        try:
            # Money Control Company page
            url = f'https://www.moneycontrol.com/india/stockpricequote/{ticker}'

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                html = response.text

                # Financial metrics patterns
                patterns = {
                    'IMP-M03-I01': r'Sales.*?([0-9,]+(?:\.[0-9]+)?)\s*Cr',
                    'IMP-M03-I02': r'Net Profit.*?([0-9,]+(?:\.[0-9]+)?)\s*Cr',
                    'IMP-M03-I03': r'Total Assets.*?([0-9,]+(?:\.[0-9]+)?)\s*Cr',
                    'IMP-M16-I07': r'Debt.*?([0-9,]+(?:\.[0-9]+)?)\s*Cr',
                    'IMP-M16-I08': r'Reserves.*?([0-9,]+(?:\.[0-9]+)?)\s*Cr',
                }

                for indicator_id, pattern in patterns.items():
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        data[indicator_id] = f"{match.group(1)} Cr"

        except Exception as e:
            pass  # Silent fail for Money Control

        return data

    def scrape_nse_india(self, ticker: str) -> Dict[str, str]:
        """Scrape from NSE India"""
        data = {}

        try:
            # NSE Quote API
            url = f'https://www.nseindia.com/api/quote-equity?symbol={ticker}'

            # NSE requires specific headers
            self.session.headers.update({
                'Accept': 'application/json',
                'Referer': 'https://www.nseindia.com/'
            })

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                json_data = response.json()

                # Extract available data
                if 'priceInfo' in json_data:
                    price_info = json_data['priceInfo']
                    if 'lastPrice' in price_info:
                        data['IMP-M03-I08'] = f"Rs {price_info['lastPrice']}"

                if 'info' in json_data:
                    info = json_data['info']
                    if 'pdSectorPe' in info:
                        data['IMP-M16-I09'] = f"{info['pdSectorPe']}"

        except Exception as e:
            pass  # Silent fail for NSE

        return data

    def scrape_bse_india(self, ticker: str) -> Dict[str, str]:
        """Scrape from BSE India"""
        data = {}

        try:
            # BSE Company page
            url = f'https://www.bseindia.com/stock-share-price/stockreach.aspx?scripcd={ticker}'

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                html = response.text

                # Extract financial data
                patterns = {
                    'IMP-M03-I09': r'Market Cap.*?([0-9,]+(?:\.[0-9]+)?)',
                    'IMP-M03-I10': r'Enterprise Value.*?([0-9,]+(?:\.[0-9]+)?)',
                }

                for indicator_id, pattern in patterns.items():
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        data[indicator_id] = f"{match.group(1)} Cr"

        except Exception as e:
            pass  # Silent fail for BSE

        return data

    def scrape_company_website(self, website: str) -> Dict[str, str]:
        """Scrape ESG data from company website"""
        data = {}

        try:
            # Try common ESG page URLs
            esg_urls = [
                f"{website}/sustainability",
                f"{website}/esg",
                f"{website}/csr",
                f"{website}/investors/sustainability",
                f"{website}/about/sustainability"
            ]

            for url in esg_urls:
                try:
                    response = self.session.get(url, timeout=10)

                    if response.status_code == 200:
                        html = response.text

                        # Look for ESG commitments
                        if any(term in html.lower() for term in ['carbon neutral', 'net zero', 'sustainability']):
                            data['IMP-M05-I05'] = "Sustainability commitment found"

                        # Look for renewable energy mentions
                        renewable_match = re.search(r'([0-9]+)\s*%.*?renewable', html, re.IGNORECASE)
                        if renewable_match:
                            data['IMP-M06-I02'] = f"{renewable_match.group(1)}%"

                        break  # Found valid ESG page

                except:
                    continue

        except Exception as e:
            pass  # Silent fail for website

        return data

def scrape_missing_for_company(company_id: int, year: int = 2024):
    """Main function to scrape missing indicators"""

    db = get_session()

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"Company {company_id} not found")
            return 0

        # Get existing indicators
        existing_data = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        existing_indicators = {data.data_key for data in existing_data}

        # Calculate missing
        all_indicators = [f"IMP-M{m:02d}-I{i:02d}" for m in range(1, 22) for i in range(1, 16)]
        all_indicators = all_indicators[:151]
        missing_indicators = [ind for ind in all_indicators if ind not in existing_indicators]

        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE ONLINE SCRAPING")
        print(f"Company: {company.name}")
        print(f"Existing: {len(existing_indicators)}/151")
        print(f"Missing: {len(missing_indicators)}/151")
        print(f"{'='*70}")

        if not missing_indicators:
            print("No missing indicators!")
            return 0

        # Scrape from all sources
        scraper = ComprehensiveOnlineScraper()
        online_data = scraper.scrape_all_sources(company, missing_indicators)

        # Store in database
        stored = 0
        for indicator_id, value in online_data.items():
            if indicator_id in missing_indicators:  # Only store missing ones
                scraped_data = ScrapedData(
                    company_id=company_id,
                    year=year,
                    source='comprehensive_online_scraping',
                    data_key=indicator_id,
                    data_value=value
                )
                db.add(scraped_data)
                stored += 1

        db.commit()

        print(f"\n{'='*70}")
        print(f"STORED: {stored} new indicators from online sources")
        print(f"NEW TOTAL: {len(existing_indicators) + stored}/151")
        print(f"{'='*70}")

        return stored

    finally:
        db.close()

if __name__ == "__main__":
    # Test with ITC
    company_id = 30
    year = 2024

    count = scrape_missing_for_company(company_id, year)
    print(f"\nFINAL: {count} indicators scraped from online sources")
