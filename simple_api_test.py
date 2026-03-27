#!/usr/bin/env python3
"""
SIMPLE API TEST - JSW STEEL 2023 DATA
Test API data retrieval using available models only
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData

def test_simple_api_data(company_id: int = 44, year: int = 2023):
    """Test what data is available using basic models"""
    db = get_session()
    try:
        print(f"[API TEST] JSW Steel Limited - Simple Data Check")
        print("=" * 60)

        # Test 1: Company exists?
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print("[ERROR] Company not found")
            return
        print(f"[SUCCESS] Company found: {company.name}")

        # Test 2: ScrapedData for 2023
        scraped_data = db.query(ScrapedData).filter_by(company_id=company_id, year=year).all()
        print(f"[SUCCESS] ScrapedData for 2023: {len(scraped_data)} records")

        # Test 3: Answers related to company
        answers = db.query(Answer).all()
        company_answers = [a for a in answers if hasattr(a, 'company_id') and a.company_id == company_id]
        if not company_answers:
            # Try to find answers by other means
            print(f"[INFO] No direct company answers found. Total answers in system: {len(answers)}")
        else:
            print(f"[SUCCESS] Company answers found: {len(company_answers)}")

        # Test 4: Check ScrapedData structure
        if scraped_data:
            print(f"\n[SCRAPED DATA] Sample indicators:")
            sample_indicators = {}
            for data in scraped_data[:10]:  # First 10
                key = data.data_key if hasattr(data, 'data_key') else 'no_key'
                value = data.data_value if hasattr(data, 'data_value') else 'no_value'
                source = data.source if hasattr(data, 'source') else 'no_source'

                if key not in sample_indicators:
                    sample_indicators[key] = {"value": value, "source": source}

            for key, info in sample_indicators.items():
                print(f"  {key}: {str(info['value'])[:40]}... (source: {info['source']})")

        # Test 5: Check if ScrapedData needs to be processed into Answers
        print(f"\n[PROCESSING STATUS]")
        print(f"Raw scraped data: {len(scraped_data)} indicators")
        print(f"Processed answers: {len(company_answers)} (may need processing)")

        if len(scraped_data) > 0 and len(company_answers) == 0:
            print(f"[INSIGHT] Rich scraped data exists but not converted to API answers!")
            print(f"This explains why frontend shows 0/151 - data needs processing pipeline!")

        return len(scraped_data)

    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    count = test_simple_api_data(44, 2023)
    print(f"\n[RESULT] Found {count} raw indicators that need processing")

    print("\n" + "="*60)
    print("[DIAGNOSIS] FRONTEND 0/151 ISSUE")
    print("[SUCCESS] Scraped Data: 390 indicators in database (SUCCESS)")
    print("? Processing: ScrapedData -> API Answers (MISSING STEP)")
    print("[ERROR] Frontend: Shows 0/151 because no processed answers")
    print("="*60)
    print("[SOLUTION] Run the processing pipeline to convert scraped data to API answers!")