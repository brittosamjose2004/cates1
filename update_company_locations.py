#!/usr/bin/env python3
"""Get company office locations and update lat/long indicators in database"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session
import json

# Predefined company locations (City, State, Country format for easy geocoding)
COMPANY_LOCATIONS = {
    "HCL Technologies Ltd": {"city": "Noida", "country": "India", "lat": 28.5244, "lon": 77.1050},
    "Infosys Ltd": {"city": "Bengaluru", "country": "India", "lat": 12.9352, "lon": 77.6245},
    "Tata Consultancy Services Ltd": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "Wipro Ltd": {"city": "Bengaluru", "country": "India", "lat": 12.9352, "lon": 77.6245},
    "Bajaj Finance Ltd": {"city": "Pune", "country": "India", "lat": 18.5204, "lon": 73.8567},
    "Hindustan Unilever Ltd": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "Bharti Airtel Ltd": {"city": "New Delhi", "country": "India", "lat": 28.7041, "lon": 77.1025},
    "Kotak Mahindra Bank Ltd": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "Nestle India Ltd": {"city": "Gurugram", "country": "India", "lat": 28.4595, "lon": 77.0266},
    "NTPC LIMITED": {"city": "New Delhi", "country": "India", "lat": 28.7041, "lon": 77.1025},
    "State Bank of India": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "ICICI BANK LIMITED": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "NDTV LIMITED": {"city": "New Delhi", "country": "India", "lat": 28.7041, "lon": 77.1025},
    "NETWORK18 MEDIA & INVESTMENTS LIMITED": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "NYKAA FASHION LIMITED": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "GUJARAT GAS LIMITED": {"city": "Gandhinagar", "country": "India", "lat": 23.2156, "lon": 72.6369},
    "DABUR INDIA LIMITED": {"city": "Ghaziabad", "country": "India", "lat": 28.6692, "lon": 77.4538},
    "COAL INDIA LIMITED": {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    "COMPREHENSIVE ESG TEST COMPANY": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "JSW Steel Limited": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "Godrej Industries Limited": {"city": "Mumbai", "country": "India", "lat": 19.0825, "lon": 72.8563},
    "Infosys Limited": {"city": "Bengaluru", "country": "India", "lat": 12.9352, "lon": 77.6245},
    "BANDHAN BANK LIMITED": {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    "Reliance Industries Limited": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
    "TATA STEEL LIMITED": {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    "ITC LIMITED": {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    "EMAMI LIMITED": {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    "APOLLO HOSPITALS ENTERPRISE LIMITED": {"city": "Chennai", "country": "India", "lat": 13.1986, "lon": 80.2841},
    "HCL TECHNOLOGIES FRANCE": {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522},
    "NIPPON LIFE INDIA ASSET MANAGEMENT LIMITED": {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
}

def update_company_location_indicators():
    """Update latitude and longitude indicators for all companies"""
    db = get_session()
    
    try:
        companies = db.query(Company).all()
        print(f"Updating company locations for {len(companies)} companies...\n")
        
        updated_count = 0
        
        for company in companies:
            # Find matching location
            location_data = None
            
            # Exact match first
            if company.name in COMPANY_LOCATIONS:
                location_data = COMPANY_LOCATIONS[company.name]
            else:
                # Try partial match
                for key, loc in COMPANY_LOCATIONS.items():
                    if key.upper() in company.name.upper():
                        location_data = loc
                        break
            
            if not location_data:
                print(f"⚠️  {company.name}: No location data found")
                continue
            
            lat = location_data['lat']
            lon = location_data['lon']
            city = location_data['city']
            
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
                
                # Update or create latitude indicator
                lat_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I01"
                ).first()
                
                if lat_answer:
                    lat_answer.answer_value = str(lat)
                    lat_answer.source = f"company_office_location ({city})"
                else:
                    lat_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I01",
                        answer_value=str(lat),
                        answer_unit="Decimal degrees",
                        confidence=1.0,
                        source=f"company_office_location ({city})",
                        is_verified=True
                    )
                    db.add(lat_answer)
                
                # Update or create longitude indicator
                lon_answer = db.query(Answer).filter_by(
                    session_id=session.id,
                    indicator_id="IMP-M22-I02"
                ).first()
                
                if lon_answer:
                    lon_answer.answer_value = str(lon)
                    lon_answer.source = f"company_office_location ({city})"
                else:
                    lon_answer = Answer(
                        session_id=session.id,
                        company_id=company.id,
                        year=year,
                        indicator_id="IMP-M22-I02",
                        answer_value=str(lon),
                        answer_unit="Decimal degrees",
                        confidence=1.0,
                        source=f"company_office_location ({city})",
                        is_verified=True
                    )
                    db.add(lon_answer)
                
                db.commit()
                updated_count += 1
                print(f"✓ {company.name} (FY{year}): Office at {city}")
                print(f"    Location: ({lat}, {lon})")
        
        print(f"\n✅ Updated {updated_count} company location records")
        
        # Save summary to file
        summary = {}
        for company in companies:
            loc = COMPANY_LOCATIONS.get(company.name)
            if loc:
                summary[company.name] = {
                    "latitude": loc['lat'],
                    "longitude": loc['lon'],
                    "city": loc['city'],
                    "country": loc['country']
                }
        
        with open('company_office_locations.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Saved location summary to: company_office_locations.json")
        
    finally:
        db.close()

if __name__ == "__main__":
    update_company_location_indicators()
