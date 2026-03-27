#!/usr/bin/env python3
"""
Web scraper to fetch real company locations and geocode them
Integrates with backend to store lat/long in database
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from bs4 import BeautifulSoup
import time
import json
from typing import Dict, Tuple, Optional

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

class CompanyLocationScraper:
    """Scrape company locations from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.geocoded_data = {}
    
    def scrape_company_location(self, company_name: str) -> Optional[Dict]:
        """Scrape company location from Google Knowledge Graph via search"""
        try:
            # Search for company headquarters using search
            search_query = f"{company_name} headquarters location"
            
            print(f"  Scraping: {company_name}...")
            
            # Try to fetch from Wikipedia first (more reliable coordinates)
            wiki_data = self._scrape_wikipedia(company_name)
            if wiki_data:
                return wiki_data
            
            # Try company database
            company_data = self._scrape_company_info(company_name)
            if company_data:
                return company_data
            
            return None
            
        except Exception as e:
            print(f"    Error scraping {company_name}: {str(e)}")
            return None
    
    def _scrape_wikipedia(self, company_name: str) -> Optional[Dict]:
        """Scrape company location from Wikipedia"""
        try:
            # Search Wikipedia
            search_url = f"https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': company_name,
                'format': 'json'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            results = response.json().get('query', {}).get('search', [])
            
            if not results:
                return None
            
            # Get first result
            page_title = results[0]['title']
            
            # Fetch page content
            page_url = f"https://en.wikipedia.org/w/api.php"
            page_params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'extracts|pageprops',
                'explaintext': True,
                'format': 'json'
            }
            
            page_response = self.session.get(page_url, params=page_params, timeout=10)
            pages = page_response.json().get('query', {}).get('pages', {})
            page_data = list(pages.values())[0]
            
            extract = page_data.get('extracts', '')
            
            # Try to find coordinates in page
            if 'coordinates' in page_data.get('pageprops', {}):
                coords = page_data['pageprops']['coordinates'][0]
                return {
                    'source': 'wikipedia',
                    'latitude': coords.get('lat'),
                    'longitude': coords.get('lon'),
                    'page': page_title
                }
            
            # Parse location from text
            location = self._extract_location_from_text(extract)
            if location:
                return {
                    'source': 'wikipedia',
                    'location_text': location,
                    'page': page_title
                }
            
        except Exception as e:
            print(f"    Wikipedia error for {company_name}: {str(e)}")
        
        return None
    
    def _scrape_company_info(self, company_name: str) -> Optional[Dict]:
        """Scrape company info from business databases"""
        try:
            # Try crunchbase-like public info
            search_url = "https://www.google.com/search"
            params = {
                'q': f"{company_name} headquarters address coordinates"
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for knowledge panel data
            kp = soup.find('div', {'data-sokoban-container': True})
            if kp:
                text = kp.get_text()
                location = self._extract_location_from_text(text)
                if location:
                    return {
                        'source': 'google_knowledge_panel',
                        'location_text': location
                    }
            
        except Exception as e:
            print(f"    Google search error for {company_name}: {str(e)}")
        
        return None
    
    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location info from text"""
        try:
            # Look for location patterns
            lines = text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['headquarters', 'located', 'based in', 'office']):
                    return line.strip()
        except:
            pass
        return None
    
    def geocode_location(self, location_text: str, company_name: str = "") -> Optional[Tuple[float, float]]:
        """Convert location text to lat/long using geopy"""
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut
            
            geocoder = Nominatim(user_agent="impactree_scraper")
            
            # Geocode the location
            location = geocoder.geocode(location_text, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
            
        except Exception as e:
            print(f"    Geocoding error for '{location_text}': {str(e)}")
        
        return None
    
    def scrape_all_companies(self) -> Dict:
        """Scrape locations for all companies in database"""
        db = get_session()
        
        try:
            companies = db.query(Company).all()
            print(f"\nScraping {len(companies)} companies for location data...\n")
            
            results = {}
            
            for company in companies:
                print(f"\n[{companies.index(company) + 1}/{len(companies)}] {company.name}")
                
                # Scrape location
                location_data = self.scrape_company_location(company.name)
                
                if location_data:
                    print(f"  Source: {location_data.get('source')}")
                    
                    # If we have coordinates already
                    if 'latitude' in location_data and 'longitude' in location_data:
                        lat = location_data['latitude']
                        lon = location_data['longitude']
                        print(f"  Found coordinates: ({lat}, {lon})")
                        results[company.name] = {
                            'latitude': lat,
                            'longitude': lon,
                            'source': location_data['source']
                        }
                    # If we have location text, geocode it
                    elif 'location_text' in location_data:
                        location_text = location_data['location_text']
                        print(f"  Location: {location_text}")
                        
                        coords = self.geocode_location(location_text, company.name)
                        if coords:
                            lat, lon = coords
                            print(f"  Geocoded: ({lat:.4f}, {lon:.4f})")
                            results[company.name] = {
                                'latitude': lat,
                                'longitude': lon,
                                'source': 'web_scraped_geocoded'
                            }
                else:
                    print(f"  No location data found")
                
                # Rate limiting
                time.sleep(2)
            
            return results
        
        finally:
            db.close()


def update_database_with_scraped_locations(scraped_data: Dict):
    """Update database with scraped location data"""
    db = get_session()
    
    try:
        print(f"\n\nUpdating database with {len(scraped_data)} scraped locations...\n")
        
        updated_count = 0
        
        for company_name, location_info in scraped_data.items():
            company = db.query(Company).filter_by(name=company_name).first()
            
            if not company:
                print(f"⚠️  Company not found: {company_name}")
                continue
            
            lat = location_info['latitude']
            lon = location_info['longitude']
            source = location_info['source']
            
            # Get all years for this company
            years = db.query(QuestionnaireSession.year).filter_by(company_id=company.id).distinct().all()
            
            for year_row in years:
                year = year_row[0]
                
                # Get or create session
                session = db.query(QuestionnaireSession).filter_by(
                    company_id=company.id,
                    year=year,
                    standard="ALL"
                ).first()
                
                if not session:
                    session = QuestionnaireSession(
                        company_id=company.id,
                        year=year,
                        standard="ALL"
                    )
                    db.add(session)
                    db.commit()
                
                # Update latitude
                lat_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I01"
                ).first()
                
                if lat_answer:
                    lat_answer.answer_value = str(lat)
                    lat_answer.source = source
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=0.9,
                        source=source,
                        is_verified=False
                    )
                    db.add(lat_answer)
                
                # Update longitude
                lon_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I02"
                ).first()
                
                if lon_answer:
                    lon_answer.answer_value = str(lon)
                    lon_answer.source = source
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=0.9,
                        source=source,
                        is_verified=False
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_count += 1
                print(f"  ✓ {company_name} (FY{year}): ({lat:.4f}, {lon:.4f})")
        
        print(f"\n✅ Updated {updated_count} indicator records with scraped data")
        
        # Save results to file
        with open('scraped_company_locations.json', 'w') as f:
            json.dump(scraped_data, f, indent=2)
        
        print(f"✓ Saved to: scraped_company_locations.json")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("="*80)
    print("COMPANY LOCATION WEB SCRAPER")
    print("="*80)
    
    scraper = CompanyLocationScraper()
    
    # Scrape all companies
    scraped_locations = scraper.scrape_all_companies()
    
    print(f"\n\nscraped {len(scraped_locations)} companies successfully")
    
    # Update database
    if scraped_locations:
        update_database_with_scraped_locations(scraped_locations)
    
    print("\n" + "="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
