#!/usr/bin/env python3
"""Extract and geocode company location data from headquarters"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.models import Company
from backend.database.db import get_session

# Get all companies from database
db = get_session()

companies = db.query(Company).all()
print(f"Found {len(companies)} companies\n")
print("Company Locations (HQ):")
print("-" * 80)

location_data = {}

for company in companies:
    hq = company.headquarters or "Not specified"
    location_data[company.name] = {
        "headquarters": hq,
        "sector": company.sector or "Unknown",
        "exchange": company.exchange or "N/A"
    }
    print(f"{company.name:50} | {hq}")

db.close()

# Now we'll use these addresses to geocode
print("\n" + "=" * 80)
print("GEOCODING ADDRESSES TO GET LATITUDE & LONGITUDE")
print("=" * 80 + "\n")

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    import time
    
    geocoder = Nominatim(user_agent="impactree_geocoder")
    
    geocoded_locations = {}
    
    for company_name, data in location_data.items():
        hq = data['headquarters']
        
        if hq == "Not specified":
            print(f"⚠️  {company_name}: No address available")
            continue
        
        try:
            # Geocode the address
            location = geocoder.geocode(hq, timeout=10)
            
            if location:
                geocoded_locations[company_name] = {
                    "address": hq,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "full_address": location.address
                }
                print(f"✓ {company_name}")
                print(f"  Address: {hq}")
                print(f"  Coordinates: ({location.latitude:.4f}, {location.longitude:.4f})")
                print(f"  Verified: {location.address}\n")
            else:
                print(f"✗ {company_name}: Could not geocode '{hq}'\n")
            
            # Rate limiting
            time.sleep(1)
            
        except GeocoderTimedOut:
            print(f"⏱️  {company_name}: Geocoding timeout\n")
            continue
        except Exception as e:
            print(f"❌ {company_name}: Error {str(e)}\n")
            continue
    
    print(f"\n{'='*80}")
    print(f"Successfully geocoded {len(geocoded_locations)} companies")
    print(f"{'='*80}\n")
    
    # Save to a file for later use
    import json
    with open('geocoded_company_locations.json', 'w') as f:
        json.dump(geocoded_locations, f, indent=2)
    
    print(f"✓ Saved geocoded data to: geocoded_company_locations.json\n")
    
    # Print summary
    print("Geocoded Company Locations (Lat, Lon):")
    print("-" * 80)
    for company_name, data in sorted(geocoded_locations.items()):
        print(f"{company_name:50} ({data['latitude']:.4f}, {data['longitude']:.4f})")

except ImportError:
    print("❌ geopy not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "geopy"])
    print("\nPlease run this script again after installation.")
