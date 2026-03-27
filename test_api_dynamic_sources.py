#!/usr/bin/env python3
"""
TEST FIXED API ENDPOINT
Test that the company detail API returns correct dynamic sources
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json

def test_api_endpoint():
    """Test the fixed company detail API endpoint"""

    print("=" * 80)
    print("TESTING FIXED API ENDPOINT")
    print("=" * 80)

    # Test the company detail API that frontend uses
    base_url = "http://localhost:8000"  # Assuming backend is running
    company_id = 26  # Bank of Baroda
    year = 2023

    try:
        # Make API request as frontend would
        response = requests.get(f"{base_url}/api/companies/{company_id}?year={year}")

        if response.status_code == 200:
            data = response.json()

            print(f"✓ API Response successful for Bank of Baroda")
            print(f"Company: {data.get('name')}")
            print(f"Year used: {data.get('year')}")

            # Check indicator sources
            indicators = data.get('indicators', [])
            print(f"Total indicators: {len(indicators)}")

            # Group by source
            source_counts = {}
            dynamic_indicators = []

            for indicator in indicators:
                source = indicator.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1

                # Check for dynamic sources
                if 'dynamic' in source or 'enhanced' in source:
                    dynamic_indicators.append({
                        'id': indicator.get('id'),
                        'source': source,
                        'value': indicator.get('value', '')[:50] + '...'
                    })

            print(f"\nAPI Response Sources:")
            for source, count in source_counts.items():
                print(f"  {source}: {count} indicators")

            print(f"\nDynamic Sources Found: {len(dynamic_indicators)}")
            if dynamic_indicators:
                for indicator in dynamic_indicators:
                    print(f"  ✓ {indicator['id']}: {indicator['source']}")
                    print(f"    Value: {indicator['value']}")
                print(f"\n🎉 SUCCESS: Frontend should now show dynamic sources!")
                return True
            else:
                print(f"  ⚠️  No dynamic sources in API response")
                print(f"  Check if pipeline was run to create Answer records with dynamic sources")
                return False

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Backend not running on {base_url}")
        print(f"Start backend with: cd backend && python -m uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_direct_database():
    """Test database has correct data"""

    print(f"\n" + "=" * 80)
    print("CHECKING DATABASE DIRECTLY")
    print("=" * 80)

    try:
        from backend.database.db import get_session
        from backend.database.models import Answer, ScrapedData

        db = get_session()

        # Check Answer records
        answers = db.query(Answer).filter_by(company_id=26, year=2023).all()

        answer_sources = {}
        for answer in answers:
            source = answer.source
            answer_sources[source] = answer_sources.get(source, 0) + 1

        print(f"Answer Records (Database):")
        for source, count in answer_sources.items():
            print(f"  {source}: {count} indicators")

        # Check ScrapedData records
        scraped = db.query(ScrapedData).filter_by(company_id=26, year=2023).all()

        scraped_sources = {}
        for record in scraped:
            source = record.source
            scraped_sources[source] = scraped_sources.get(source, 0) + 1

        print(f"\nScrapedData Records (Database):")
        for source, count in scraped_sources.items():
            print(f"  {source}: {count} indicators")

        # Both should have dynamic sources
        dynamic_answers = [s for s in answer_sources.keys() if 'dynamic' in s]
        dynamic_scraped = [s for s in scraped_sources.keys() if 'dynamic' in s]

        if dynamic_answers and dynamic_scraped:
            print(f"\n✓ SUCCESS: Database has dynamic sources in both tables")
            return True
        elif dynamic_answers:
            print(f"\n⚠️  PARTIAL: Dynamic sources in Answer table only")
            return True
        elif dynamic_scraped:
            print(f"\n⚠️  PARTIAL: Dynamic sources in ScrapedData table only")
            return False
        else:
            print(f"\n❌ MISSING: No dynamic sources in database")
            return False

        db.close()

    except Exception as e:
        print(f"Database Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("TESTING API ENDPOINT AND DATABASE")
    print("=" * 80)

    # Test 1: Database
    db_success = test_direct_database()

    # Test 2: API
    api_success = test_api_endpoint()

    print("\n" + "=" * 80)
    print("FINAL DIAGNOSIS")
    print("=" * 80)

    if api_success:
        print("🎉 COMPLETE SUCCESS!")
        print("✓ Dynamic sources working in API")
        print("✓ Frontend should show correct sources")
        print("\nNext Steps:")
        print("1. Refresh your browser (clear cache)")
        print("2. Navigate to Bank of Baroda")
        print("3. Check that sources now show 'Dynamic ESG', 'Dynamic IT Patterns'")

    elif db_success:
        print("⚠️  PARTIAL SUCCESS")
        print("✓ Dynamic sources in database")
        print("❌ API not returning dynamic sources")
        print("\nTroubleshooting:")
        print("1. Restart the backend server")
        print("2. Check if API endpoint fixes are applied")
        print("3. Check year parameter in API call")

    else:
        print("❌ NEEDS DEBUGGING")
        print("❌ No dynamic sources in database")
        print("\nAction Required:")
        print("1. Run pipeline to regenerate data with dynamic sources")
        print("2. Check comprehensive_pipeline.py integration")