#!/usr/bin/env python3
"""Populate latitude and longitude indicators for all companies"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from backend.database.models import Company, Answer, QuestionnaireSession
from backend.database.db import get_session

# Latitude and longitude data for Indian companies (HQ locations)
company_locations = {
    "Godrej Industries Limited": (19.0825, 72.8563),        # Mumbai
    "TATA STEEL LIMITED": (22.5726, 88.3639),               # Kolkata
    "JSW STEEL LIMITED": (15.3855, 73.8284),               # Goa/Bangalore (HQ varies)
    "APOLLO HOSPITALS ENTERPRISE LIMITED": (13.1986, 80.2841),  # Chennai
    "ASIAN PAINTS (INDIA) LIMITED": (19.1136, 72.8697),   # Mumbai
    "INFOSYS LIMITED": (12.9352, 77.6245),                 # Bangalore
    "TCS": (19.0760, 72.8777),                             # Mumbai
    "HCL TECHNOLOGIES": (28.5244, 77.1050),                # NCR
    "WIPRO LIMITED": (12.9352, 77.6245),                   # Bangalore
    "RELIANCE INDUSTRIES": (19.0760, 72.8777),              # Mumbai
    "NESTLÉ INDIA LIMITED": (19.0760, 72.8777),             # Mumbai
    "ITC LIMITED": (22.5726, 88.3639),                      # Kolkata
    "EMAMI LIMITED": (22.5726, 88.3639),                    # Kolkata
    "NIPPON LIFE INDIA": (19.0760, 72.8777),                # Mumbai
    "BANDHAN BANK LIMITED": (22.5726, 88.3639),             # Kolkata
}

def populate_location_indicators():
    """Add latitude and longitude values for indicators"""
    db = get_session()
    
    try:
        companies = db.query(Company).all()
        print(f"Found {len(companies)} companies")
        
        added_count = 0
        for company in companies:
            # Try to find location data for this company
            location = company_locations.get(company.name)
            if not location:
                # Try partial match
                for key, loc in company_locations.items():
                    if key.upper() in company.name.upper() or company.name.upper() in key.upper():
                        location = loc
                        break
            
            if location:
                lat, lon = location
                
                # For each year in the database for this company
                years = db.query(QuestionnaireSession.year).filter_by(company_id=company.id).distinct().all()
                
                for year_row in years:
                    year = year_row[0]
                    
                    # Get or create session for this company-year
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
                    
                    # Add latitude indicator
                    lat_answer = db.query(Answer).filter_by(
                        session_id=session.id,
                        indicator_id="IMP-M22-I01"
                    ).first()
                    
                    if not lat_answer:
                        lat_answer = Answer(
                            session_id=session.id,
                            company_id=company.id,
                            year=year,
                            indicator_id="IMP-M22-I01",
                            answer_value=str(lat),
                            answer_unit="Decimal degrees",
                            confidence=1.0,
                            source="company_headquarters_db",
                            is_verified=True
                        )
                        db.add(lat_answer)
                    
                    # Add longitude indicator
                    lon_answer = db.query(Answer).filter_by(
                        session_id=session.id,
                        indicator_id="IMP-M22-I02"
                    ).first()
                    
                    if not lon_answer:
                        lon_answer = Answer(
                            session_id=session.id,
                            company_id=company.id,
                            year=year,
                            indicator_id="IMP-M22-I02",
                            answer_value=str(lon),
                            answer_unit="Decimal degrees",
                            confidence=1.0,
                            source="company_headquarters_db",
                            is_verified=True
                        )
                        db.add(lon_answer)
                    
                    db.commit()
                    added_count += 1
                    print(f"  ✓ {company.name} (FY{year}): Lat={lat}, Lon={lon}")
        
        print(f"\n✅ Populated {added_count} company location records")
        
    finally:
        db.close()

if __name__ == "__main__":
    populate_location_indicators()
