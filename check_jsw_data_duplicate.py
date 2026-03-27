#!/usr/bin/env python3
"""
JSW STEEL DATA COMPARISON - 2020 vs 2021
Check if data for JSW Steel Limited is identical between years (potential data quality issue)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData
from data_source_tracker import DataSourceTracker

def compare_jsw_steel_years(company_id: int = 44, year1: int = 2020, year2: int = 2021):
    """Compare JSW Steel data between two years to check for duplicates"""

    print(f"JSW STEEL DATA COMPARISON: {year1} vs {year2}")
    print("Checking if data is identical (potential data quality issue)")
    print("=" * 80)

    db = get_session()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            print(f"[ERROR] Company {company_id} not found")
            return

        print(f"Company: {company.name}")
        print(f"Comparing years: {year1} vs {year2}")
        print("-" * 60)

        # Get data for both years
        data_2020 = db.query(ScrapedData).filter_by(company_id=company_id, year=year1).all()
        data_2021 = db.query(ScrapedData).filter_by(company_id=company_id, year=year2).all()

        print(f"Data records found:")
        print(f"  {year1}: {len(data_2020)} records")
        print(f"  {year2}: {len(data_2021)} records")

        if len(data_2020) == 0 and len(data_2021) == 0:
            print(f"[WARNING] No data found for either year")
            return

        # Convert to dictionaries for comparison
        def data_to_dict(data_list):
            result = {}
            for item in data_list:
                key = item.data_key if hasattr(item, 'data_key') else 'unknown'
                value = item.data_value if hasattr(item, 'data_value') else None
                source = item.source if hasattr(item, 'source') else 'unknown'
                result[key] = {
                    'value': value,
                    'source': source
                }
            return result

        dict_2020 = data_to_dict(data_2020)
        dict_2021 = data_to_dict(data_2021)

        # Compare the data
        print(f"\n[COMPARISON ANALYSIS]")
        print("-" * 60)

        # Check if they have the same indicators
        keys_2020 = set(dict_2020.keys())
        keys_2021 = set(dict_2021.keys())

        common_keys = keys_2020.intersection(keys_2021)
        only_2020 = keys_2020 - keys_2021
        only_2021 = keys_2021 - keys_2020

        print(f"Indicator comparison:")
        print(f"  Common indicators: {len(common_keys)}")
        print(f"  Only in {year1}: {len(only_2020)}")
        print(f"  Only in {year2}: {len(only_2021)}")

        if len(only_2020) > 0:
            print(f"  Indicators only in {year1}: {sorted(list(only_2020))[:5]}{'...' if len(only_2020) > 5 else ''}")
        if len(only_2021) > 0:
            print(f"  Indicators only in {year2}: {sorted(list(only_2021))[:5]}{'...' if len(only_2021) > 5 else ''}")

        # Check for identical values
        identical_values = 0
        different_values = 0
        value_comparisons = []

        for key in common_keys:
            val_2020 = dict_2020[key]['value']
            val_2021 = dict_2021[key]['value']

            if val_2020 == val_2021:
                identical_values += 1
            else:
                different_values += 1
                value_comparisons.append({
                    'indicator': key,
                    f'{year1}_value': str(val_2020)[:50] + ('...' if len(str(val_2020)) > 50 else ''),
                    f'{year2}_value': str(val_2021)[:50] + ('...' if len(str(val_2021)) > 50 else '')
                })

        print(f"\n[VALUE COMPARISON]")
        print("-" * 60)
        print(f"Identical values: {identical_values}")
        print(f"Different values: {different_values}")

        if len(common_keys) > 0:
            identical_percentage = (identical_values / len(common_keys)) * 100
            print(f"Identical percentage: {identical_percentage:.1f}%")

            # Determine if this looks like duplicated data
            if identical_percentage > 90 and len(common_keys) > 10:
                print(f"\n⚠️  WARNING: HIGH SIMILARITY ({identical_percentage:.1f}%)")
                print(f"This suggests data may be duplicated between {year1} and {year2}")
            elif identical_percentage > 70:
                print(f"\n⚠️  CAUTION: MODERATE SIMILARITY ({identical_percentage:.1f}%)")
                print(f"Some data may be duplicated between {year1} and {year2}")
            else:
                print(f"\n✅ NORMAL: LOW SIMILARITY ({identical_percentage:.1f}%)")
                print(f"Data appears to be genuinely different between {year1} and {year2}")

        # Show some examples of different values
        if value_comparisons and len(value_comparisons) <= 10:
            print(f"\n[SAMPLE DIFFERENCES]")
            print("-" * 60)
            for comp in value_comparisons[:5]:
                print(f"{comp['indicator']}:")
                print(f"  {year1}: {comp[f'{year1}_value']}")
                print(f"  {year2}: {comp[f'{year2}_value']}")
                print()

        # Check sources
        sources_2020 = set(dict_2020[k]['source'] for k in dict_2020.keys())
        sources_2021 = set(dict_2021[k]['source'] for k in dict_2021.keys())

        print(f"[SOURCES COMPARISON]")
        print("-" * 60)
        print(f"Sources in {year1}: {sorted(sources_2020)}")
        print(f"Sources in {year2}: {sorted(sources_2021)}")

        if sources_2020 == sources_2021:
            print(f"⚠️  WARNING: IDENTICAL SOURCES")
            print(f"Same sources used for both years - may indicate data duplication")
        else:
            print(f"✅ DIFFERENT SOURCES: Data likely from different extraction runs")

        return {
            'identical_percentage': identical_percentage if len(common_keys) > 0 else 0,
            'common_indicators': len(common_keys),
            'identical_values': identical_values,
            'different_values': different_values,
            'same_sources': sources_2020 == sources_2021
        }

    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def detailed_data_analysis():
    """Perform detailed analysis of JSW Steel data across multiple years"""
    print(f"\n" + "=" * 80)
    print("DETAILED JSW STEEL DATA ANALYSIS - MULTIPLE YEARS")
    print("=" * 80)

    # Check what years have data
    db = get_session()
    try:
        years_with_data = db.query(ScrapedData.year).filter_by(company_id=44).distinct().all()
        years = sorted([y[0] for y in years_with_data if y[0]])

        print(f"JSW Steel has data for years: {years}")

        # Compare each consecutive pair of years
        for i in range(len(years) - 1):
            year1, year2 = years[i], years[i + 1]
            print(f"\n{'='*40}")
            result = compare_jsw_steel_years(44, year1, year2)

            if result and result['identical_percentage'] > 80:
                print(f"🚨 POTENTIAL DATA QUALITY ISSUE DETECTED!")
                print(f"Years {year1} and {year2} have {result['identical_percentage']:.1f}% identical data")

    except Exception as e:
        print(f"[ERROR] Detailed analysis failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Main comparison: 2020 vs 2021
    result = compare_jsw_steel_years(44, 2020, 2021)

    # Detailed analysis across all years
    detailed_data_analysis()

    print(f"\n" + "=" * 80)
    print("JSW STEEL DATA COMPARISON COMPLETE")
    print("=" * 80)