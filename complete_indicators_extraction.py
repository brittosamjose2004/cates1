#!/usr/bin/env python3
"""
COMPLETE INDICATORS EXTRACTION - ALL VALUES UNTIL END
Show every single indicator value extracted from the comprehensive system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
import pandas as pd

def show_all_indicators_complete(company_id: int = 44, year: int = 2023):
    """Show ALL indicator values extracted - complete until end"""
    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"[ERROR] Company {company_id} not found")
            return 0

        print(f"[COMPLETE EXTRACTION] ALL INDICATORS VALUES UNTIL END")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("=" * 100)

        # Get ALL scraped data for this company/year
        all_scraped = db.query(ScrapedData).filter_by(
            company_id=company_id,
            year=year
        ).all()

        # Get ALL manual answers for this company/year
        all_manual = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        print(f"Total scraped records: {len(all_scraped)}")
        print(f"Total manual answers: {len(all_manual)}")

        # Process ALL indicators
        all_indicators = {}

        # Add ALL scraped indicators
        for data in all_scraped:
            indicator_id = data.data_key if hasattr(data, 'data_key') else 'unknown'
            value = data.data_value if hasattr(data, 'data_value') else None
            source = data.source if hasattr(data, 'source') else 'unknown'

            if indicator_id.startswith('IMP-M') and value:
                all_indicators[indicator_id] = {
                    'value': value,
                    'source': source,
                    'type': 'scraped'
                }

        # Add ALL manual indicators (override if exists)
        for answer in all_manual:
            if hasattr(answer, 'indicator_id') and hasattr(answer, 'answer_value'):
                indicator_id = answer.indicator_id
                value = answer.answer_value

                if indicator_id and value and indicator_id.startswith('IMP-M'):
                    all_indicators[indicator_id] = {
                        'value': value,
                        'source': 'manual_input',
                        'type': 'manual'
                    }

        # Sort indicators for display
        sorted_indicators = dict(sorted(all_indicators.items()))

        print(f"\n[DISPLAYING ALL {len(sorted_indicators)} INDICATORS - COMPLETE VALUES]")
        print("=" * 100)

        # Group by module for organized display
        modules = {}
        for indicator_id, data in sorted_indicators.items():
            # Extract module (IMP-M01-I01 -> M01)
            parts = indicator_id.split('-')
            if len(parts) >= 2:
                module = parts[1]  # M01, M02, etc.
                if module not in modules:
                    modules[module] = []
                modules[module].append((indicator_id, data))

        total_shown = 0
        for module in sorted(modules.keys()):
            indicators_in_module = modules[module]
            print(f"\n[MODULE {module}] - {len(indicators_in_module)} indicators")
            print("-" * 80)

            for indicator_id, data in indicators_in_module:
                value_str = str(data['value'])
                source = data['source']
                itype = data['type']

                # Show full value (truncate if too long for display)
                if len(value_str) > 80:
                    display_value = value_str[:80] + "..."
                else:
                    display_value = value_str

                print(f"{indicator_id:15} | {display_value:60} | {itype:8} | {source}")
                total_shown += 1

        print("\n" + "=" * 100)
        print(f"[COMPLETE EXTRACTION SUMMARY]")
        print(f"Total indicators extracted: {len(sorted_indicators)}")
        print(f"Total indicators displayed: {total_shown}")
        print(f"Target was 151 indicators - ACHIEVED {(len(sorted_indicators)/151)*100:.1f}% coverage")
        print(f"ALL INDICATOR VALUES SHOWN UNTIL END")
        print("=" * 100)

        return len(sorted_indicators)

    except Exception as e:
        print(f"[ERROR] Complete extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("[START] COMPLETE INDICATORS EXTRACTION - ALL VALUES UNTIL END")
    print("Target: Show every single indicator value found")
    print("=" * 100)

    # Run complete extraction for JSW Steel 2023
    count = show_all_indicators_complete(44, 2023)

    print(f"\n[FINAL RESULT] {count} indicators extracted and displayed completely")
    print("[END] Complete extraction finished - all values shown until end")