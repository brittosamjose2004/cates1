#!/usr/bin/env python3
"""
Use OpenStreetMap (Nominatim) to get exact company headquarters and office locations
with latitude and longitude coordinates
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json
import time
from typing import Dict, List, Optional, Tuple

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

class OSMLocationFinder:
    """Use OpenStreetMap Nominatim API to find exact company locations"""
    
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Impactree-ESG-Company-Locator'
        })
    
    def search_osm_location(self, query: str) -> Optional[Dict]:
        """Search for a location using OpenStreetMap Nominatim API"""
        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            print(f"    Searching OSM for: {query}...", end=" ", flush=True)
            
            response = self.session.get(self.nominatim_url, params=params, timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                
                if results and len(results) > 0:
                    result = results[0]
                    lat = float(result.get('lat'))
                    lon = float(result.get('lon'))
                    name = result.get('name', query)
                    address = result.get('display_name', '')
                    
                    print(f"Found!")
                    
                    return {
                        'name': name,
                        'latitude': lat,
                        'longitude': lon,
                        'address': address,
                        'osm_id': result.get('osm_id'),
                        'osm_type': result.get('osm_type')
                    }
                else:
                    print(f"No results")
                    return None
            else:
                print(f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def find_company_location(self, company_name: str, address: str = None) -> Optional[Dict]:
        """Find exact location of a company"""
        
        # Try with company name first if headquarters address is available
        if address and address.strip() not in ['NA', 'Not specified', 'APAC', 'EU', '']:
            # Search for headquarters address
            search_query = f"{company_name} headquarters {address}"
            result = self.search_osm_location(search_query)
            
            if result:
                return result
            
            # Fall back to just the address
            result = self.search_osm_location(address)
            if result:
                return result
        
        # Just search by company name
        search_query = f"{company_name} headquarters"
        return self.search_osm_location(search_query)
    
    def find_all_company_locations(self) -> Dict:
        """Find locations for all companies in database"""
        db = get_session()
        
        try:
            companies = db.query(Company).all()
            print(f"Finding {len(companies)} companies using OpenStreetMap...\n")
            
            results = {}
            found_count = 0
            
            for idx, company in enumerate(companies):
                print(f"[{idx+1}/{len(companies)}] {company.name}")
                
                location = self.find_company_location(company.name, company.headquarters)
                
                if location:
                    results[company.name] = {
                        'company_id': company.id,
                        'headquarters': company.headquarters,
                        'latitude': location['latitude'],
                        'longitude': location['longitude'],
                        'location_name': location['name'],
                        'address': location['address'],
                        'osm_id': location['osm_id'],
                        'osm_type': location['osm_type']
                    }
                    found_count += 1
                    print(f"    Exact coords: ({location['latitude']:.6f}, {location['longitude']:.6f})")
                    print(f"    Address: {location['address'][:60]}...")
                
                print()
                
                # Rate limiting - respect OSM's terms
                time.sleep(1.5)
            
            print(f"\n✓ Found locations for {found_count}/{len(companies)} companies")
            
            return results
        
        finally:
            db.close()


def update_database_with_osm_locations(osm_data: Dict):
    """Update database with OpenStreetMap coordinates"""
    db = get_session()
    
    try:
        print(f"\nUpdating database with {len(osm_data)} OpenStreetMap locations...\n")
        
        updated_count = 0
        
        for company_name, location_info in osm_data.items():
            company = db.query(Company).filter_by(name=company_name).first()
            
            if not company:
                print(f"⚠️  Company not found: {company_name}")
                continue
            
            lat = location_info['latitude']
            lon = location_info['longitude']
            address = location_info['address']
            
            print(f"Updating: {company_name}")
            print(f"  OpenStreetMap Address: {address}")
            print(f"  Exact Coordinates: ({lat:.6f}, {lon:.6f})")
            
            # Get all years for this company
            years = db.query(QuestionnaireSession.year).filter_by(company_id=company.id).distinct().all()
            
            if not years:
                print(f"    Warning: No years found\n")
                continue
            
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
                
                # Update latitude indicator (IMP-M22-I01)
                lat_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I01"
                ).first()
                
                if lat_answer:
                    lat_answer.answer_value = str(lat)
                    lat_answer.source = "openstreetmap_nominatim"
                    lat_answer.confidence = 0.98
                    lat_answer.is_verified = True
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=0.98,
                        source="openstreetmap_nominatim",
                        is_verified=True
                    )
                    db.add(lat_answer)
                
                # Update longitude indicator (IMP-M22-I02)
                lon_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I02"
                ).first()
                
                if lon_answer:
                    lon_answer.answer_value = str(lon)
                    lon_answer.source = "openstreetmap_nominatim"
                    lon_answer.confidence = 0.98
                    lon_answer.is_verified = True
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=0.98,
                        source="openstreetmap_nominatim",
                        is_verified=True
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_count += 1
            
            print(f"    Updated {len(years)} year records\n")
        
        print(f"Total updated: {updated_count} coordinate records\n")
        
        # Save results to file
        json_data = {}
        for company, data in osm_data.items():
            json_data[company] = {
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'headquarters': data['headquarters'],
                'osm_address': data['address'],
                'osm_id': data['osm_id'],
                'osm_type': data['osm_type']
            }
        
        with open('openstreetmap_company_locations.json', 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"Saved to: openstreetmap_company_locations.json\n")
        
    finally:
        db.close()


def main():
    print("="*80)
    print("COMPANY LOCATION FINDER - OPENSTREETMAP NOMINATIM")
    print("="*80 + "\n")
    
    finder = OSMLocationFinder()
    
    # Find all company locations
    osm_locations = finder.find_all_company_locations()
    
    if osm_locations:
        print("\n" + "="*80)
        print(f"Successfully found {len(osm_locations)} company locations")
        print("="*80)
        
        # Update database
        update_database_with_osm_locations(osm_locations)
        
        print("="*80)
        print("OPENSTREETMAP LOCATION UPDATE COMPLETE")
        print("="*80)
        
        # Show sample results
        print("\nSample Exact Locations from OpenStreetMap:")
        print("-" * 80)
        for company, data in list(osm_locations.items())[:5]:
            print(f"\n{company}")
            print(f"  Headquarters: {data['headquarters']}")
            print(f"  OSM Address: {data['address']}")
            print(f"  Exact Coordinates: ({data['latitude']:.6f}, {data['longitude']:.6f})")
        
    else:
        print("No locations found")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
