#!/usr/bin/env python3
"""
CHECK 151 INDICATORS MAPPING
Check how the 390 database records map to the 151 ESG indicators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, ScrapedData

def check_151_indicators_mapping(company_id: int = 44, year: int = 2023):
    """Check how database records map to the 151 ESG indicators"""
    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        print(f"[ANALYSIS] 151 ESG Indicators Mapping")
        print(f"Company: {company.name}")
        print(f"Year: {year}")
        print("=" * 80)

        # Get all data for this company/year
        all_data = db.query(ScrapedData).filter_by(company_id=company_id, year=year).all()
        print(f"Total database records: {len(all_data)}")

        # Group by indicator ID pattern
        indicator_groups = {}
        imp_indicators = []
        other_indicators = []

        for data in all_data:
            key = data.data_key if hasattr(data, 'data_key') else 'no_key'

            if key.startswith('IMP-M'):
                imp_indicators.append(key)

                # Extract module (e.g., IMP-M01-I01 -> M01)
                parts = key.split('-')
                if len(parts) >= 2:
                    module = parts[1]  # M01, M02, etc.
                    if module not in indicator_groups:
                        indicator_groups[module] = []
                    indicator_groups[module].append(key)
            else:
                other_indicators.append(key)

        print(f"\nIMP-M indicators (151 ESG system): {len(imp_indicators)}")
        print(f"Other indicators: {len(other_indicators)}")

        # Show breakdown by module
        if indicator_groups:
            print(f"\nBreakdown by ESG Module:")
            for module in sorted(indicator_groups.keys()):
                indicators = sorted(set(indicator_groups[module]))
                print(f"  {module}: {len(indicators)} indicators")

                # Show first few indicators for each module
                for indicator in indicators[:3]:
                    sample_data = next((d for d in all_data if (d.data_key if hasattr(d, 'data_key') else 'no_key') == indicator), None)
                    if sample_data:
                        value = sample_data.data_value if hasattr(sample_data, 'data_value') else 'no_value'
                        print(f"    {indicator}: {value[:50]}...")  # Show first 50 chars of value

                if len(indicators) > 3:
                    print(f"    ... and {len(indicators)-3} more")
                print()

        # Count unique IMP-M indicators
        unique_imp = set(imp_indicators)
        print(f"Unique IMP-M indicators: {len(unique_imp)}")
        print(f"Expected 151 indicators vs Found {len(unique_imp)}")
        print(f"Coverage: {(len(unique_imp)/151)*100:.1f}%")

        # Show some examples of other indicators
        if other_indicators:
            print(f"\nOther indicator examples:")
            unique_others = sorted(set(other_indicators))
            for indicator in unique_others[:10]:
                sample_data = next((d for d in all_data if (d.data_key if hasattr(d, 'data_key') else 'no_key') == indicator), None)
                if sample_data:
                    value = sample_data.data_value if hasattr(sample_data, 'data_value') else 'no_value'
                    print(f"  {indicator}: {value[:30]}...")

        return len(unique_imp)

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    count = check_151_indicators_mapping(44, 2023)
    print(f"\n[RESULT] Found {count}/151 ESG indicators for JSW Steel 2023")