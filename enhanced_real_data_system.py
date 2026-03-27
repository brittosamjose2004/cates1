#!/usr/bin/env python3
"""
ENHANCED REAL DATA ONLY ESG SYSTEM - COMPREHENSIVE + NO SYNTHETIC DATA
Combines comprehensive database extraction with strict real-data-only approach
Uses: Comprehensive Database Scraped Data > Manual Data > Fresh Document Data > Historical Data > Empty
Never generates artificial/synthetic values - only uses authentic extracted data
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, QuestionnaireSession
import pandas as pd
from datetime import datetime

def load_all_151_indicators():
    """Load all 151 indicators from CSV"""
    script_dir = Path(__file__).parent
    csv_path = script_dir / "Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    df = pd.read_csv(str(csv_path))
    df_clean = df[df.iloc[:,0].str.startswith('IMP-M', na=False)].copy()

    indicators = []
    for _, row in df_clean.iterrows():
        indicator_id = str(row.iloc[0]).strip()
        module = str(row.iloc[1]).strip()
        indicator_name = str(row.iloc[2]).strip()
        indicators.append({
            'id': indicator_id,
            'module': module,
            'name': indicator_name
        })

    return indicators

def extract_comprehensive_real_data(company_id: int, year: int, db_session, allow_historical_fallback: bool = False) -> dict:
    """
    Extract comprehensive real ESG data from all authentic sources.

    Priority order (all real data sources):
    1. COMPREHENSIVE DATABASE SCRAPED DATA (highest - proven real extraction)
    2. Manual/Input data (user entered)
    3. Fresh document extraction (new uploads)
    4. Historical data from other years (optional, disabled by default)

    Returns only REAL data - NO synthetic generation.
    """
    print(f"[ENHANCED] Extracting comprehensive real ESG data...")
    print(f"Company ID: {company_id}, Year: {year}")
    print("=" * 80)

    real_data = {}
    stats = {
        'comprehensive_db': 0,
        'manual': 0,
        'fresh_docs': 0,
        'historical': 0,
        'missing': 0
    }

    # STEP 1: Load comprehensive database scraped data (PRIORITY 1)
    print("[PRIORITY 1] Loading comprehensive database scraped data...")
    comprehensive_data = db_session.query(ScrapedData).filter_by(
        company_id=company_id,
        year=year
    ).all()

    print(f"Found {len(comprehensive_data)} comprehensive database records")

    # Process comprehensive database data
    for entry in comprehensive_data:
        indicator_id = entry.data_key if hasattr(entry, 'data_key') else 'unknown'
        value = entry.data_value if hasattr(entry, 'data_value') else None
        source = entry.source if hasattr(entry, 'source') else 'comprehensive_db'

        if indicator_id.startswith('IMP-M') and value:
            real_data[indicator_id] = {
                'value': value,
                'source_priority': 'comprehensive_database',
                'source_detail': source,
                'confidence': 0.95,  # High confidence for proven extraction
                'year': year
            }
            stats['comprehensive_db'] += 1
            print(f"COMPREHENSIVE: {indicator_id}: {str(value)[:50]}...")

    # STEP 2: Check for manual/input data (PRIORITY 2)
    print(f"\n[PRIORITY 2] Checking manual/input data...")
    manual_answers = db_session.query(Answer).filter(
        Answer.company_id == company_id,
        Answer.year == year
    ).all()

    manual_count = 0
    for answer in manual_answers:
        # Check for manual answers with values
        if hasattr(answer, 'answer_value') and answer.answer_value and answer.indicator_id:
            indicator_id = answer.indicator_id

            # Manual data has highest priority - override comprehensive data if exists
            if indicator_id.startswith('IMP-M'):
                real_data[indicator_id] = {
                    'value': answer.answer_value,
                    'source_priority': 'manual',
                    'source_detail': 'user_input',
                    'confidence': 1.0,  # Highest confidence for manual data
                    'year': year
                }
                manual_count += 1
                print(f"MANUAL: {indicator_id}: {str(answer.answer_value)[:50]}...")

    print(f"Found {manual_count} manual entries")
    stats['manual'] = manual_count

    # STEP 3: Fresh document extraction (PRIORITY 3)
    print(f"\n[PRIORITY 3] Checking fresh document extraction...")
    fresh_entries = db_session.query(ScrapedData).filter(
        ScrapedData.company_id == company_id,
        ScrapedData.year == year,
        ScrapedData.source.like('%fresh%')
    ).all()

    print(f"Found {len(fresh_entries)} fresh document extractions")
    for entry in fresh_entries:
        indicator_id = entry.data_key if hasattr(entry, 'data_key') else 'unknown'
        value = entry.data_value if hasattr(entry, 'data_value') else None

        # Only add if not already covered by comprehensive data
        if indicator_id.startswith('IMP-M') and value and indicator_id not in real_data:
            real_data[indicator_id] = {
                'value': value,
                'source_priority': 'fresh_document',
                'source_detail': entry.source,
                'confidence': 0.85,
                'year': year
            }
            stats['fresh_docs'] += 1
            print(f"FRESH: {indicator_id}: {str(value)[:50]}...")

    # STEP 4: Historical data as fallback (PRIORITY 4, optional)
    print(f"\n[PRIORITY 4] Historical data fallback...")
    if not allow_historical_fallback:
        print("Historical fallback disabled (strict selected-year mode)")
    else:
        other_years = [year-1, year-2, year-3, year+1, year+2]  # Try nearby years

        for check_year in other_years:
            if len(real_data) >= 151:  # Stop if we have enough data
                break

            historical_data = db_session.query(ScrapedData).filter_by(
                company_id=company_id,
                year=check_year
            ).all()

            for entry in historical_data:
                indicator_id = entry.data_key if hasattr(entry, 'data_key') else 'unknown'
                value = entry.data_value if hasattr(entry, 'data_value') else None

                # Only add if not already covered
                if indicator_id.startswith('IMP-M') and value and indicator_id not in real_data:
                    real_data[indicator_id] = {
                        'value': value,
                        'source_priority': 'historical',
                        'source_detail': f"year_{check_year}_{entry.source}",
                        'confidence': 0.75,
                        'year': check_year
                    }
                    stats['historical'] += 1
                    if stats['historical'] <= 3:  # Show first few examples
                        print(f"HISTORICAL: {indicator_id}: {str(value)[:50]}... (from {check_year})")

    return real_data, stats

def process_enhanced_real_data_only(company_id: int, year: int, db_session=None, allow_historical_fallback: bool = False) -> int:
    """
    Enhanced real data only processing that includes comprehensive database data.
    Returns count of indicators processed with REAL data sources only.
    """
    db = db_session if db_session else get_session()
    external_session = db_session is None

    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"[ERROR] Company {company_id} not found")
            return 0

        print(f"\n[ENHANCED REAL DATA ONLY SYSTEM]")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print(f"Target: 151 ESG indicators")
        print("=" * 80)

        # Load all 151 target indicators
        indicators = load_all_151_indicators()
        print(f"Target indicators: {len(indicators)}")

        # Extract comprehensive real data for selected year.
        real_data, stats = extract_comprehensive_real_data(
            company_id,
            year,
            db,
            allow_historical_fallback=allow_historical_fallback,
        )

        print(f"\n" + "="*80)
        print(f"ENHANCED REAL DATA ONLY - SUMMARY")
        print(f"="*80)
        print(f"SUCCESS: Comprehensive database data: {stats['comprehensive_db']}")
        print(f"SUCCESS: Manual data preserved: {stats['manual']}")
        print(f"SUCCESS: Fresh document data: {stats['fresh_docs']}")
        print(f"SUCCESS: Historical data used: {stats['historical']}")

        total_found = len(real_data)
        missing = len(indicators) - total_found
        print(f"MISSING: Missing (no real data): {missing}")
        print(f"TOTAL COVERAGE: {total_found}/{len(indicators)} ({(total_found/len(indicators)*100):.1f}%)")
        print(f"NO SYNTHETIC DATA GENERATED")

        # AUTOMATIC DATA SOURCES SAVING
        try:
            from automatic_data_saver import pipeline_auto_save_data_sources
            print(f"\n[AUTO-SAVE] Automatically saving data sources...")
            auto_save_result = pipeline_auto_save_data_sources(company_id, year)
            if auto_save_result:
                print(f"[AUTO-SAVE] SUCCESS Saved {auto_save_result['total_indicators']} indicators from {auto_save_result['total_sources']} sources")
            else:
                print(f"[AUTO-SAVE] WARNING Auto-save skipped")
        except Exception as auto_save_error:
            print(f"[AUTO-SAVE] ERROR Failed: {str(auto_save_error)}")

        if total_found < 50:
            print(f"\nTo improve coverage:")
            print(f"   1. Upload sustainability reports/ESG documents")
            print(f"   2. Add manual data entry for key indicators")
            print(f"   3. Verify comprehensive extraction completed")

        return total_found

    except Exception as e:
        print(f"[ERROR] Enhanced real data processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if external_session:
            db.close()

# Original function for backwards compatibility
def process_real_data_only(company_id: int, year: int, db_session=None, allow_historical_fallback: bool = False) -> int:
    """Original function - redirects to enhanced version"""
    return process_enhanced_real_data_only(
        company_id,
        year,
        db_session,
        allow_historical_fallback=allow_historical_fallback,
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Real Data Only ESG Processing")
    parser.add_argument("--company-id", type=int, required=True, help="Company ID")
    parser.add_argument("--year", type=int, required=True, help="Year to process")

    args = parser.parse_args()

    # Test the enhanced system
    print("[TEST] Enhanced Real Data Only System")
    print("=" * 60)

    result = process_enhanced_real_data_only(args.company_id, args.year)
    print(f"\n[RESULT] {result} indicators processed with enhanced real data only system")