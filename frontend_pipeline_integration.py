#!/usr/bin/env python3
"""
FRONTEND PIPELINE INTEGRATION - TARGET 151 INDICATORS
Integration module for frontend run pipeline to show exact 151 indicators progress
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
        print(f"[WARNING] CSV file not found at: {csv_path}")
        return []

    try:
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
    except Exception as e:
        print(f"[ERROR] Failed to load target indicators: {e}")
        return []

def get_pipeline_151_status(company_id: int, year: int):
    """
    Get exact status of 151 target indicators for frontend pipeline display
    Returns: (found_count, total_count, coverage_percent, module_stats)
    """
    db = get_session()
    try:
        # Load target indicators
        target_indicators = load_target_151_indicators()
        if not target_indicators:
            return 0, 151, 0.0, {}

        total_target = len(target_indicators)

        # Get all available data
        all_scraped = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        all_manual = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        # Create lookup for available data
        available_data = {}

        # Add scraped data
        for data in all_scraped:
            indicator_id = data.data_key if hasattr(data, 'data_key') else None
            value = data.data_value if hasattr(data, 'data_value') else None
            if indicator_id and value:
                available_data[indicator_id] = {
                    'value': value,
                    'source': 'scraped'
                }

        # Add manual data (higher priority)
        for answer in all_manual:
            if hasattr(answer, 'indicator_id') and hasattr(answer, 'answer_value'):
                indicator_id = answer.indicator_id
                value = answer.answer_value
                if indicator_id and value:
                    available_data[indicator_id] = {
                        'value': value,
                        'source': 'manual'
                    }

        # Check how many target indicators we have
        found_count = 0
        module_stats = {}
        missing_indicators = []

        for target in target_indicators:
            indicator_id = target['id']
            module = target['module']

            if module not in module_stats:
                module_stats[module] = {'found': 0, 'total': 0}
            module_stats[module]['total'] += 1

            if indicator_id in available_data:
                found_count += 1
                module_stats[module]['found'] += 1
            else:
                missing_indicators.append(indicator_id)

        coverage_percent = (found_count / total_target) * 100 if total_target > 0 else 0

        return found_count, total_target, coverage_percent, module_stats, missing_indicators

    except Exception as e:
        print(f"[ERROR] Pipeline 151 status failed: {e}")
        return 0, 151, 0.0, {}, []
    finally:
        db.close()

def format_pipeline_progress_message(company_id: int, year: int):
    """
    Format progress message for pipeline logs showing exact target 151 status
    """
    try:
        found_count, total_count, coverage_percent, module_stats, missing = get_pipeline_151_status(company_id, year)

        if coverage_percent >= 99:
            status_emoji = "EXCELLENT"
        elif coverage_percent >= 90:
            status_emoji = "VERY GOOD"
        elif coverage_percent >= 75:
            status_emoji = "GOOD"
        else:
            status_emoji = "PARTIAL"

        # Create main progress message
        main_msg = f"TARGET 151 INDICATORS: {found_count}/{total_count} found ({coverage_percent:.1f}% coverage) - {status_emoji}"

        # Create detailed breakdown
        details = []
        if module_stats:
            complete_modules = sum(1 for stats in module_stats.values() if stats['found'] == stats['total'])
            partial_modules = sum(1 for stats in module_stats.values() if 0 < stats['found'] < stats['total'])
            empty_modules = sum(1 for stats in module_stats.values() if stats['found'] == 0)

            details.append(f"Modules: {complete_modules} complete, {partial_modules} partial, {empty_modules} empty")

        if missing:
            if len(missing) <= 5:
                details.append(f"Missing: {', '.join(missing)}")
            else:
                details.append(f"Missing: {len(missing)} indicators (first 3: {', '.join(missing[:3])}...)")

        return main_msg, details

    except Exception as e:
        return f"TARGET 151 INDICATORS: Error checking status - {str(e)}", []

if __name__ == "__main__":
    # Test the integration
    print("[TEST] Frontend Pipeline Integration - Target 151 Indicators")
    print("=" * 80)

    # Test with JSW Steel 2023
    msg, details = format_pipeline_progress_message(44, 2023)
    print(f"Main message: {msg}")
    for detail in details:
        print(f"Detail: {detail}")

    print("\n[TEST COMPLETE]")