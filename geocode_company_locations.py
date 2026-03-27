#!/usr/bin/env python3
"""
Simple location scraper using company headquarters from database
Geocode to get real latitude/longitude coordinates
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import time
from typing import Dict, Optional, Tuple

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

class SimpleLocationGeocoder:
    """Geocode company headquarters to latitude/longitude"""
    
    def __init__(self):
        try:
            from geopy.geocoders import Nominatim
            self.geocoder = Nominatim(user_agent="impactree_location_scraper")
            print("Geocoder initialized successfully\n")
        except ImportError:
            print("Installing geopy...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "geopy", "-q"])
            from geopy.geocoders import Nominatim
            self.geocoder = Nominatim(user_agent="impactree_location_scraper")
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Geocode an address to get coordinates"""
        if not address or address.strip() in ['NA', 'Not specified', 'APAC', 'EU', '']:
            return None
        
        try:
            from geopy.exc import GeocoderTimedOut
            
            print(f"    Geocoding: {address}")
            location = self.geocoder.geocode(address, timeout=15)
            
            if location:
                return (location.latitude, location.longitude, location.address)
            
        except GeocoderTimedOut:
            print(f"    Geocoding timeout for: {address}")
        except Exception as e:
            print(f"    Geocoding error: {str(e)}")
        
        return None
    
    def geocode_all_companies(self) -> Dict:
        """Geocode all companies using their headquarters address"""
        db = get_session()
        
        try:
            companies = db.query(Company).all()
            print(f"Geocoding {len(companies)} companies from database headquarters...\n")
            
            results = {}
            success_count = 0
            
            for idx, company in enumerate(companies):
                hq = company.headquarters
                
                if not hq or hq.strip() in ['NA', 'Not specified', 'APAC', 'EU', '']:
                    print(f"[{idx+1}/{len(companies)}] {company.name}: No HQ address")
                    continue
                
                print(f"[{idx+1}/{len(companies)}] {company.name}")
                
                geocoded = self.geocode_address(hq)
                
                if geocoded:
                    lat, lon, full_address = geocoded
                    print(f"    Found: ({lat:.4f}, {lon:.4f})")
                    print(f"    Address: {full_address}\n")
                    
                    results[company.name] = {
                        'company_id': company.id,
                        'headquarters': hq,
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded_address': full_address,
                        'source': 'nominatim_geocoded'
                    }
                    success_count += 1
                else:
                    print(f"    Could not geocode\n")
                
                # Rate limiting - be respectful to Nominatim
                time.sleep(1.5)
            
            print(f"\n✓ Successfully geocoded {success_count}/{len(companies)} companies")
            
            return results
        
        finally:
            db.close()


def update_database_with_coordinates(geocoded_data: Dict):
    """Update database with geocoded coordinates"""
    db = get_session()
    
    try:
        print(f"\nUpdating database with {len(geocoded_data)} geocoded locations...\n")
        
        updated_count = 0
        
        for company_name, location_info in geocoded_data.items():
            company = db.query(Company).filter_by(name=company_name).first()
            
            if not company:
                print(f"⚠️  Company not found: {company_name}")
                continue
            
            lat = location_info['latitude']
            lon = location_info['longitude']
            source = location_info['source']
            hq = location_info['headquarters']
            
            print(f"Updating: {company_name}")
            print(f"  HQ: {hq}")
            print(f"  Coordinates: ({lat:.4f}, {lon:.4f})")
            
            # Get all years for this company
            years = db.query(QuestionnaireSession.year).filter_by(company_id=company.id).distinct().all()
            
            if not years:
                print(f"  Warning: No years found for this company")
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
                    lat_answer.source = source
                    lat_answer.confidence = 0.95
                    lat_answer.is_verified = True
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=0.95,
                        source=source,
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
                    lon_answer.source = source
                    lon_answer.confidence = 0.95
                    lon_answer.is_verified = True
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=0.95,
                        source=source,
                        is_verified=True
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_count += 1
            
            print(f"  Updated {len(years)} year records")
            print()
        
        print(f"\nTotal updated: {updated_count} indicator records")
        
        # Save results
        with open('geocoded_company_locations.json', 'w') as f:
            json_data = {}
            for company, data in geocoded_data.items():
                json_data[company] = {
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'headquarters': data['headquarters'],
                    'geocoded_address': data['geocoded_address'],
                    'source': data['source']
                }
            json.dump(json_data, f, indent=2)
        
        print(f"\nSaved to: geocoded_company_locations.json")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("="*80)
    print("COMPANY LOCATION GEOCODER")
    print("="*80 + "\n")
    
    try:
        geocoder = SimpleLocationGeocoder()
        
        # Geocode all companies
        geocoded_locations = geocoder.geocode_all_companies()
        
        if geocoded_locations:
            print("\n" + "="*80)
            print(f"Successfully geocoded {len(geocoded_locations)} companies")
            print("="*80)
            
            # Update database
            update_database_with_coordinates(geocoded_locations)
            
            print("\n" + "="*80)
            print("GEOCODING AND DATABASE UPDATE COMPLETE")
            print("="*80)
        else:
            print("\nNo locations geocoded")
    
    except KeyboardInterrupt:
        print("\n\nGeocoding interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
