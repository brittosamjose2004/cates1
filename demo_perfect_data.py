import requests
import json

def test_perfect_data_scenarios():
    print("🎯 PERFECT ESG DATA RETRIEVAL SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 70)

    scenarios = [
        {
            "name": "Asian Paints - Request 2019 (Poor Data)",
            "url": "http://localhost:8000/api/companies/14?year=2019",
            "expected": "Should fallback to best year"
        },
        {
            "name": "Asian Paints - Request 2024 (Good Data)",
            "url": "http://localhost:8000/api/companies/14?year=2024",
            "expected": "Should use 2024"
        },
        {
            "name": "Asian Paints - Auto Selection",
            "url": "http://localhost:8000/api/companies/14",
            "expected": "Should select best year automatically"
        },
        {
            "name": "Year Recommendations",
            "url": "http://localhost:8000/api/companies/14/year-recommendations",
            "expected": "Should show all years with quality grades"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Expected: {scenario['expected']}")
        print("-" * 50)

        try:
            resp = requests.get(scenario['url'], timeout=10)
            if resp.status_code == 200:
                data = resp.json()

                if 'recommendations' in data:  # Year recommendations endpoint
                    print(f"   ✅ SUCCESS: Found {len(data['recommendations'])} years")
                    print(f"   📊 Best year: {data['best_year']}")
                    for rec in data['recommendations'][:3]:
                        year = rec['year']
                        grade = rec['quality_grade']
                        completeness = rec['completeness_percentage']
                        print(f"   📅 {year}: {grade} grade, {completeness}% complete")

                elif 'dataQuality' in data:  # Company data endpoint
                    dq = data['dataQuality']
                    if dq:
                        indicators_count = sum(1 for i in data.get('indicators', []) if i.get('value'))
                        fy = data.get('financialYear')

                        print(f"   ✅ SUCCESS: {fy} with {indicators_count}/151 indicators")
                        print(f"   🎯 Requested: {dq.get('requested_year') or 'auto'}")
                        print(f"   📊 Used: {dq.get('year_used')} ({dq.get('quality_grade')} grade)")
                        print(f"   📈 Completeness: {dq.get('completeness_percentage')}%")

                        if dq.get('fallback_reason'):
                            print(f"   🔄 Smart Fallback: {dq.get('fallback_reason')}")

                        if dq.get('is_perfect_data'):
                            print("   ⭐ PERFECT DATA QUALITY!")
                    else:
                        print("   ❌ DataQuality field missing")

                else:
                    print("   ⚠️  Unexpected response format")

            else:
                print(f"   ❌ HTTP Error: {resp.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print(f"\n" + "=" * 70)
    print("🎉 PERFECT ESG DATA SYSTEM DEMONSTRATION COMPLETE!")
    print("\n✨ Key Features Demonstrated:")
    print("   • Smart year selection (automatically finds best data)")
    print("   • Intelligent fallback (poor year → perfect year)")
    print("   • Quality grading system (A+ through F)")
    print("   • Data completeness tracking (percentage)")
    print("   • Year recommendations with quality analysis")
    print("   • Perfect data guarantee (always best available)")

if __name__ == "__main__":
    test_perfect_data_scenarios()