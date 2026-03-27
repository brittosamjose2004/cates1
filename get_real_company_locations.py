#!/usr/bin/env python3
"""
Get real company locations from database headquarters and geocode to lat/long
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import time
from typing import Dict, Optional, Tuple

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

def install_geopy():
    """Install geopy if not available"""
    try:
        import geopy
    except ImportError:
        print("Installing geopy...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "geopy", "-q"])
        print("geopy installed\n")

def get_company_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """Get latitude and longitude for an address"""
    if not address or address.strip() in ['NA', 'Not specified', 'APAC', 'EU', '']:
        return None
    
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut
        
        geocoder = Nominatim(user_agent="impactree_location")
        
        print(f"    Geocoding: {address}...", end=" ", flush=True)
        location = geocoder.geocode(address, timeout=20)
        
        if location:
            print(f"OK ({location.latitude:.4f}, {location.longitude:.4f})")
            return (location.latitude, location.longitude)
        else:
            print("not found")
            return None
            
    except GeocoderTimedOut:
        print("timeout")
        return None
    except Exception as e:
        print(f"error: {str(e)}")
        return None

def main():
    print("="*80)
    print("COMPANY LOCATION GEOCODER - FROM DATABASE HEADQUARTERS")
    print("="*80 + "\n")
    
    install_geopy()
    
    db = get_session()
    
    try:
        companies = db.query(Company).all()
        print(f"Processing {len(companies)} companies...\n")
        
        updated_total = 0
        geocoded_data = {}
        
        for idx, company in enumerate(companies):
            print(f"[{idx+1}/{len(companies)}] {company.name}")
            
            hq = company.headquarters
            if not hq or hq.strip() in ['NA', 'Not specified', 'APAC', 'EU', '']:
                print(f"    No HQ address available\n")
                continue
            
            # Geocode the headquarters address
            coords = get_company_coordinates(hq)
            
            if not coords:
                print()
                continue
            
            lat, lon = coords
            
            # Get all years for this company
            years = db.query(QuestionnaireSession.year).filter_by(company_id=company.id).distinct().all()
            
            if not years:
                print(f"    No years in database\n")
                continue
            
            # Update database for each year
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
                
                # Update latitude (IMP-M22-I01)
                lat_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I01"
                ).first()
                
                if lat_answer:
                    lat_answer.answer_value = str(lat)
                    lat_answer.source = "geocoded_headquarters"
                    lat_answer.confidence = 1.0
                    lat_answer.is_verified = True
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=1.0,
                        source="geocoded_headquarters",
                        is_verified=True
                    )
                    db.add(lat_answer)
                
                # Update longitude (IMP-M22-I02)
                lon_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I02"
                ).first()
                
                if lon_answer:
                    lon_answer.answer_value = str(lon)
                    lon_answer.source = "geocoded_headquarters"
                    lon_answer.confidence = 1.0
                    lon_answer.is_verified = True
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=1.0,
                        source="geocoded_headquarters",
                        is_verified=True
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_total += 1
            
            geocoded_data[company.name] = {
                'headquarters': hq,
                'latitude': lat,
                'longitude': lon
            }
            
            print(f"    Updated {len(years)} records")
            print()
            
            # Rate limiting - be respectful to Nominatim
            time.sleep(1)
        
        print("\n" + "="*80)
        print(f"Successfully updated {updated_total} coordinate records")
        print("="*80)
        
        # Save summary
        with open('real_company_locations.json', 'w') as f:
            json.dump(geocoded_data, f, indent=2)
        
        print(f"\nSaved to: real_company_locations.json\n")
        
        # Show sample results
        if geocoded_data:
            print("Sample Results:")
            print("-" * 80)
            for company_name, data in list(geocoded_data.items())[:5]:
                print(f"{company_name:40} ({data['latitude']:.4f}, {data['longitude']:.4f})")
                print(f"  HQ: {data['headquarters']}")
                print()
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
