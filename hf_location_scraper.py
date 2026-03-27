#!/usr/bin/env python3
"""
Use Hugging Face web search API to fetch company locations and extract coordinates
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json
import time
from typing import Dict, Optional, Tuple

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

class HuggingFaceLocationScraper:
    """Use Hugging Face web search to fetch company locations"""
    
    def __init__(self):
        self.hf_space_url = "https://huggingface.co/spaces/victor/websearch"
        self.api_url = "https://victor-websearch-spaces.hf.space/api/predict"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_company_location(self, company_name: str) -> Optional[str]:
        """Search for company location using web search"""
        try:
            print(f"  Searching for: {company_name}...")
            
            # Search query for company headquarters
            query = f"{company_name} headquarters location coordinates"
            
            # Call HF web search API
            payload = {
                "data": [query]
            }
            
            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract search results
                if 'data' in result and len(result['data']) > 0:
                    search_results = result['data'][0]
                    print(f"    Found search results")
                    return search_results
            
            return None
            
        except Exception as e:
            print(f"    Error searching: {str(e)}")
            return None
    
    def extract_coordinates_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract latitude and longitude from search result text"""
        try:
            # Look for coordinate patterns like: 19.0825, 72.8563
            import re
            
            # Pattern for latitude, longitude in various formats
            patterns = [
                r'(-?\d+\.\d+),\s*(-?\d+\.\d+)',  # lat, lon
                r'latitude[:\s]+(-?\d+\.?\d*)[^0-9-]*longitude[:\s]+(-?\d+\.?\d*)',
                r'lat[:\s]+(-?\d+\.?\d*)[^0-9-]*lon[:\s]+(-?\d+\.?\d*)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    # Validate coordinates
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return (lat, lon)
            
        except Exception as e:
            print(f"    Error extracting coordinates: {str(e)}")
        
        return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address to coordinates using geopy"""
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut
            
            geocoder = Nominatim(user_agent="impactree_hf_scraper")
            location = geocoder.geocode(address, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
        
        except Exception as e:
            print(f"    Geocoding error: {str(e)}")
        
        return None
    
    def get_company_location(self, company_name: str) -> Optional[Dict]:
        """Get company location through web search and geocoding"""
        try:
            # Search for company
            search_result = self.search_company_location(company_name)
            
            if not search_result:
                return None
            
            # Try to extract coordinates directly
            coords = self.extract_coordinates_from_text(search_result)
            
            if coords:
                lat, lon = coords
                print(f"    Coordinates found: ({lat:.4f}, {lon:.4f})")
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'source': 'huggingface_websearch',
                    'search_result': search_result
                }
            
            # If no direct coordinates, try geocoding the search result
            # Extract city/country from search result
            geocoded = self.geocode_address(search_result)
            if geocoded:
                lat, lon = geocoded
                print(f"    Geocoded: ({lat:.4f}, {lon:.4f})")
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'source': 'huggingface_geocoded',
                    'search_result': search_result
                }
            
            print(f"    Could not extract coordinates")
            return None
            
        except Exception as e:
            print(f"    Error: {str(e)}")
            return None
    
    def scrape_all_companies(self) -> Dict:
        """Scrape locations for all companies"""
        db = get_session()
        
        try:
            companies = db.query(Company).all()
            print(f"Scraping {len(companies)} companies using HuggingFace web search...\n")
            
            results = {}
            success_count = 0
            
            for idx, company in enumerate(companies):
                print(f"[{idx+1}/{len(companies)}] {company.name}")
                
                location_data = self.get_company_location(company.name)
                
                if location_data:
                    results[company.name] = location_data
                    success_count += 1
                else:
                    print(f"    No location found")
                
                # Rate limiting - be respectful
                time.sleep(2)
            
            print(f"\n✓ Successfully scraped {success_count}/{len(companies)} companies")
            
            return results
        
        finally:
            db.close()


def update_database_with_scraped_data(scraped_data: Dict):
    """Update database with scraped location coordinates"""
    db = get_session()
    
    try:
        print(f"\nUpdating database with {len(scraped_data)} company locations...\n")
        
        updated_count = 0
        
        for company_name, location_info in scraped_data.items():
            company = db.query(Company).filter_by(name=company_name).first()
            
            if not company:
                print(f"⚠️  Company not found: {company_name}")
                continue
            
            lat = location_info['latitude']
            lon = location_info['longitude']
            source = location_info['source']
            
            print(f"Updating: {company_name}")
            print(f"  Coordinates: ({lat:.4f}, {lon:.4f})")
            
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
                
                # Update latitude indicator
                lat_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I01"
                ).first()
                
                if lat_answer:
                    lat_answer.answer_value = str(lat)
                    lat_answer.source = source
                    lat_answer.confidence = 0.85
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=0.85,
                        source=source,
                        is_verified=False
                    )
                    db.add(lat_answer)
                
                # Update longitude indicator
                lon_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I02"
                ).first()
                
                if lon_answer:
                    lon_answer.answer_value = str(lon)
                    lon_answer.source = source
                    lon_answer.confidence = 0.85
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=0.85,
                        source=source,
                        is_verified=False
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_count += 1
            
            print(f"  Updated {len(years)} year records")
        
        print(f"\nTotal updated: {updated_count} indicator records")
        
        # Save results
        with open('huggingface_scraped_locations.json', 'w') as f:
            # Convert for JSON serialization
            json_data = {}
            for company, data in scraped_data.items():
                json_data[company] = {
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'source': data['source']
                }
            json.dump(json_data, f, indent=2)
        
        print(f"\nSaved results to: huggingface_scraped_locations.json")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("="*80)
    print("COMPANY LOCATION SCRAPER - HUGGINGFACE WEB SEARCH")
    print("="*80 + "\n")
    
    try:
        scraper = HuggingFaceLocationScraper()
        
        # Scrape all companies
        scraped_locations = scraper.scrape_all_companies()
        
        if scraped_locations:
            print("\n" + "="*80)
            print(f"Successfully scraped {len(scraped_locations)} company locations")
            print("="*80)
            
            # Update database
            update_database_with_scraped_data(scraped_locations)
            
            print("\n" + "="*80)
            print("SCRAPING AND DATABASE UPDATE COMPLETE")
            print("="*80)
        else:
            print("\nNo locations scraped")
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
