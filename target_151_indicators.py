#!/usr/bin/env python3
"""
TARGET 151 INDICATORS EXTRACTION
Extract exactly the 151 target ESG indicators from the standard questionnaire
Show progress until we reach all 151 indicators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
import pandas as pd

def load_target_151_indicators():
    """Load the exact 151 target indicators from the standard questionnaire"""
    script_dir = Path(__file__).parent
    csv_path = script_dir / "Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    df = pd.read_csv(str(csv_path))
    df_clean = df[df.iloc[:,0].str.startswith('IMP-M', na=False)].copy()

    target_indicators = []
    for _, row in df_clean.iterrows():
        indicator_id = str(row.iloc[0]).strip()
        module = str(row.iloc[1]).strip()
        indicator_name = str(row.iloc[2]).strip()
        target_indicators.append({
            'id': indicator_id,
            'module': module,
            'name': indicator_name
        })

    return target_indicators

def extract_151_target_indicators(company_id: int = 44, year: int = 2023):
    """Extract exactly the 151 target indicators until we get all of them"""
    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"[ERROR] Company {company_id} not found")
            return 0

        print(f"[TARGET 151 INDICATORS] Extraction Until All Found")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("=" * 100)

        # Load the exact 151 target indicators
        target_indicators = load_target_151_indicators()
        print(f"Target indicators to find: {len(target_indicators)}")

        # Get all available data
        all_scraped = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        all_manual = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"Available data sources: {len(all_scraped)} scraped + {len(all_manual)} manual")
        print("=" * 100)

        # Create lookup for available data
        available_data = {}

        # Add scraped data
        for data in all_scraped:
            indicator_id = data.data_key if hasattr(data, 'data_key') else None
            value = data.data_value if hasattr(data, 'data_value') else None
            if indicator_id and value:
                available_data[indicator_id] = {
                    'value': value,
                    'source': 'scraped',
                    'detail': data.source if hasattr(data, 'source') else 'unknown'
                }

        # Add manual data (higher priority)
        for answer in all_manual:
            if hasattr(answer, 'indicator_id') and hasattr(answer, 'answer_value'):
                indicator_id = answer.indicator_id
                value = answer.answer_value
                if indicator_id and value:
                    available_data[indicator_id] = {
                        'value': value,
                        'source': 'manual',
                        'detail': 'user_input'
                    }

        print(f"[EXTRACTING] Searching for each of the 151 target indicators...")
        print("=" * 100)

        found_indicators = {}
        current_count = 0

        # Process each target indicator
        for i, target in enumerate(target_indicators, 1):
            indicator_id = target['id']
            indicator_name = target['name']
            module = target['module']

            # Check if we have data for this target indicator
            if indicator_id in available_data:
                data = available_data[indicator_id]
                found_indicators[indicator_id] = {
                    'value': data['value'],
                    'source': data['source'],
                    'detail': data['detail'],
                    'name': indicator_name,
                    'module': module
                }
                current_count += 1

                # Show progress for every indicator found
                value_str = str(data['value'])
                if len(value_str) > 60:
                    display_value = value_str[:60] + "..."
                else:
                    display_value = value_str

                print(f"[{current_count:3d}/151] {indicator_id:15} | {display_value:65} | {data['source']:8}")
            else:
                # Show missing indicators
                print(f"[MISSING] {indicator_id:15} | {indicator_name[:65]:65} | NOT_FOUND")

        print("\n" + "=" * 100)
        print(f"[EXTRACTION COMPLETE - TARGET 151 INDICATORS]")
        print(f"Found: {current_count}/151 indicators")
        print(f"Missing: {151 - current_count}/151 indicators")
        print(f"Coverage: {(current_count/151)*100:.1f}%")

        if current_count == 151:
            print(f"SUCCESS! ALL 151 TARGET INDICATORS FOUND!")
        elif current_count > 140:
            print(f"EXCELLENT! {current_count}/151 indicators found - almost complete!")
        elif current_count > 100:
            print(f"GOOD! {current_count}/151 indicators found - majority covered!")
        else:
            print(f"PARTIAL: {current_count}/151 indicators found - need more data sources!")

        print("=" * 100)

        # Show module breakdown
        module_stats = {}
        for indicator_id, data in found_indicators.items():
            module = data['module']
            if module not in module_stats:
                module_stats[module] = 0
            module_stats[module] += 1

        if module_stats:
            print(f"\n[MODULE BREAKDOWN] Indicators found by module:")
            for module in sorted(module_stats.keys()):
                count = module_stats[module]
                print(f"  {module}: {count} indicators")

        return current_count

    except Exception as e:
        print(f"[ERROR] Target 151 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("[START] TARGET 151 INDICATORS EXTRACTION")
    print("Goal: Extract exactly the 151 target ESG indicators until we get all of them")
    print("=" * 100)

    count = extract_151_target_indicators(44, 2023)

    print(f"\n[FINAL RESULT] Found {count}/151 target indicators")
    if count == 151:
        print("[SUCCESS] ALL 151 TARGET INDICATORS EXTRACTED!")
    else:
        print(f"[PROGRESS] {count}/151 indicators found - continuing until we reach 151")
    print("[END] Target 151 extraction complete")