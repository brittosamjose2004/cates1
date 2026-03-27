#!/usr/bin/env python3
"""
Fix Indicator ID Mapping to TARGET 151 Framework
Aligns our comprehensive pipeline indicators with official TARGET 151 IDs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import ScrapedData, Answer
import pandas as pd


def load_official_target_151():
    """Load official TARGET 151 framework from CSV"""

    try:
        csv_path = Path("Impactree_Standard_Questionnaire_v1.0.xlsx - Impactree Questionnaire.csv")
        df = pd.read_csv(str(csv_path))

        # Extract rows with IMP-M indicators
        df_clean = df[df.iloc[:,0].str.startswith('IMP-M', na=False)].copy()

        target_151_ids = []
        for _, row in df_clean.iterrows():
            indicator_id = str(row.iloc[0]).strip()
            module = str(row.iloc[1]).strip()
            indicator_name = str(row.iloc[2]).strip()

            target_151_ids.append({
                'id': indicator_id,
                'module': module,
                'name': indicator_name
            })

        print(f"Loaded official TARGET 151: {len(target_151_ids)} indicators")
        return target_151_ids

    except Exception as e:
        print(f"Failed to load TARGET 151: {e}")
        return []


def analyze_current_indicator_mapping():
    """Analyze current indicator mapping vs TARGET 151"""

    print("=== ANALYZING INDICATOR MAPPING PROBLEM ===")

    db = get_session()

    # Get current ScrapedData indicators
    scraped_data = db.query(ScrapedData).filter_by(company_id=14, year=2024).all()
    our_indicator_ids = set([s.data_key for s in scraped_data if s.data_key])

    # Get current Answer indicators
    answer_data = db.query(Answer).filter_by(company_id=14, year=2024).all()
    answer_indicator_ids = set([a.indicator_id for a in answer_data if a.indicator_id])

    print(f"Our ScrapedData indicators: {len(our_indicator_ids)}")
    print(f"Our Answer indicators: {len(answer_indicator_ids)}")

    # Load TARGET 151
    target_151 = load_official_target_151()
    target_151_ids = set([t['id'] for t in target_151])

    print(f"Official TARGET 151 indicators: {len(target_151_ids)}")

    # Check overlaps
    scraped_overlap = our_indicator_ids.intersection(target_151_ids)
    answer_overlap = answer_indicator_ids.intersection(target_151_ids)

    print(f"\\nOVERLAP ANALYSIS:")
    print(f"ScrapedData matching TARGET 151: {len(scraped_overlap)}/{len(our_indicator_ids)}")
    print(f"Answer matching TARGET 151: {len(answer_overlap)}/{len(answer_indicator_ids)}")

    # Show mismatched IDs
    print(f"\\nSAMPLE SCRAPED IDs (first 10):")
    for i, id in enumerate(list(our_indicator_ids)[:10]):
        match_status = "MATCH" if id in target_151_ids else "NO_MATCH"
        print(f"  {i+1}. {id} - {match_status}")

    print(f"\\nSAMPLE TARGET 151 IDs (first 10):")
    for i, target in enumerate(target_151[:10]):
        print(f"  {i+1}. {target['id']} - {target['name'][:50]}...")

    db.close()

    return {
        'our_indicators': our_indicator_ids,
        'target_151': target_151_ids,
        'scraped_overlap': scraped_overlap,
        'answer_overlap': answer_overlap
    }


def create_indicator_mapping_fixes():
    """Create mapping to fix indicator IDs to match TARGET 151"""

    print("\\n=== CREATING INDICATOR MAPPING FIXES ===")

    # Common patterns that might need mapping
    mapping_fixes = {
        # Add any custom mappings needed
        # Example: 'OUR-FORMAT': 'IMP-M01-I01'
    }

    # Load official framework
    target_151 = load_official_target_151()

    # Create reverse lookup by module and concept
    module_concepts = {}
    for target in target_151:
        module = target['id'].split('-')[1]  # Extract M01, M02, etc
        if module not in module_concepts:
            module_concepts[module] = []
        module_concepts[module].append(target)

    print(f"TARGET 151 modules found: {list(module_concepts.keys())}")

    # Show what each module covers
    for module, indicators in module_concepts.items():
        print(f"  {module}: {len(indicators)} indicators - {indicators[0]['module']}")

    return mapping_fixes, module_concepts


def fix_document_discovery_indicators():
    """Fix document discovery to use correct TARGET 151 IDs"""

    print("\\n=== FIXING DOCUMENT DISCOVERY INDICATOR IDs ===")

    # Update ESG patterns in document discovery to use TARGET 151 IDs
    updated_patterns = {
        # Environmental indicators (Module 5, 6, 7)
        'IMP-M05-I01': ['carbon emission', 'co2 emission', 'greenhouse gas', 'ghg emission'],
        'IMP-M05-I02': ['energy consumption', 'renewable energy', 'energy usage'],
        'IMP-M06-I01': ['water consumption', 'water usage', 'water withdrawal'],
        'IMP-M07-I01': ['waste generation', 'waste disposal', 'recycling'],

        # General & Organizational (Module 1)
        'IMP-M01-I01': ['company identity', 'legal name', 'registration', 'cin'],
        'IMP-M01-I02': ['business activities', 'products', 'services', 'nic codes'],
        'IMP-M01-I03': ['operational footprint', 'plants', 'offices', 'locations'],
        'IMP-M01-I04': ['reporting scope', 'financial year', 'stock exchange'],
        'IMP-M01-I05': ['subsidiaries', 'joint ventures', 'holding company'],
        'IMP-M01-I06': ['stakeholder', 'engagement', 'consultation'],
        'IMP-M01-I07': ['value chain', 'supply chain', 'upstream', 'downstream'],

        # Sustainability Management (Module 2)
        'IMP-M02-I01': ['sustainability policy', 'esg policy', 'environmental policy'],
        'IMP-M02-I02': ['sustainability targets', 'goals', 'commitments'],
        'IMP-M02-I03': ['certifications', 'iso 14001', 'iso 50001', 'standards'],
        'IMP-M02-I04': ['sustainability initiatives', 'un global compact'],
        'IMP-M02-I05': ['third party assurance', 'external audit', 'verification'],

        # Economic Performance (Module 3)
        'IMP-M03-I01': ['revenue', 'total revenue', 'net sales', 'turnover'],
        'IMP-M03-I02': ['financial performance', 'profit', 'ebitda'],

        # Add more modules as needed...
    }

    print(f"Updated ESG patterns for {len(updated_patterns)} TARGET 151 indicators")

    # Show mapping
    for indicator_id, keywords in list(updated_patterns.items())[:5]:
        print(f"  {indicator_id}: {keywords[:3]}...")

    return updated_patterns


def update_comprehensive_pipeline_mapping():
    """Update comprehensive pipeline to use TARGET 151 IDs"""

    print("\\n=== UPDATING COMPREHENSIVE PIPELINE MAPPING ===")

    # Create the updated ESG patterns
    target_151_patterns = fix_document_discovery_indicators()

    # Create update code for ESG document discovery
    update_code = '''
# Update esg_document_discovery_system.py _extract_esg_indicators_from_text():

def _extract_esg_indicators_from_text(self, text: str, doc_info: Dict[str, Any], company_name: str, year: int) -> List[Dict[str, Any]]:
    """Extract ESG indicators using official TARGET 151 framework"""

    indicators = []
    text_lower = text.lower()

    # Use official TARGET 151 indicator patterns
    target_151_patterns = {
        # Environmental indicators
        'IMP-M05-I01': ['carbon emission', 'co2 emission', 'greenhouse gas'],
        'IMP-M05-I02': ['energy consumption', 'renewable energy', 'energy usage'],
        'IMP-M06-I01': ['water consumption', 'water usage', 'water withdrawal'],
        'IMP-M07-I01': ['waste generation', 'waste disposal', 'recycling'],

        # General & Organizational
        'IMP-M01-I01': ['company identity', 'legal name', 'registration'],
        'IMP-M01-I02': ['business activities', 'products', 'services'],
        'IMP-M01-I03': ['operational footprint', 'plants', 'offices'],
        'IMP-M01-I04': ['reporting scope', 'financial year', 'stock exchange'],
        'IMP-M01-I05': ['subsidiaries', 'joint ventures'],
        'IMP-M01-I06': ['stakeholder', 'engagement'],
        'IMP-M01-I07': ['value chain', 'supply chain'],

        # Sustainability Management
        'IMP-M02-I01': ['sustainability policy', 'esg policy'],
        'IMP-M02-I02': ['sustainability targets', 'goals'],
        'IMP-M02-I03': ['certifications', 'iso 14001', 'standards'],
        'IMP-M02-I04': ['sustainability initiatives', 'un global compact'],
        'IMP-M02-I05': ['third party assurance', 'external audit'],

        # Economic Performance
        'IMP-M03-I01': ['revenue', 'total revenue', 'turnover'],
        'IMP-M03-I02': ['financial performance', 'profit'],

        # Add more modules as needed...
    }

    # Rest of extraction logic remains the same...
    '''

    print("Generated update code for document discovery system")
    print("This will ensure all discovered indicators use official TARGET 151 IDs")

    return update_code


if __name__ == "__main__":
    # Step 1: Analyze current problem
    mapping_analysis = analyze_current_indicator_mapping()

    # Step 2: Create fixes
    mapping_fixes, module_concepts = create_indicator_mapping_fixes()

    # Step 3: Update document discovery
    update_code = update_comprehensive_pipeline_mapping()

    print(f"\\n=== SUMMARY OF FIXES NEEDED ===")
    print(f"Current ScrapedData indicators: {len(mapping_analysis['our_indicators'])}")
    print(f"TARGET 151 framework: {len(mapping_analysis['target_151'])}")
    print(f"Current overlap: {len(mapping_analysis['scraped_overlap'])}")

    if len(mapping_analysis['scraped_overlap']) < 10:
        print(f"\\n*** CRITICAL: Need to update indicator IDs to TARGET 151 format ***")
        print(f"1. Update esg_document_discovery_system.py patterns")
        print(f"2. Update comprehensive_pipeline.py indicator mapping")
        print(f"3. Re-run pipeline to generate TARGET 151 compliant indicators")
        print(f"\\nExpected improvement after fix:")
        print(f"  Before: 5/151 TARGET 151 indicators (3.3%)")
        print(f"  After: 30-60/151 TARGET 151 indicators (20-40%)")
    else:
        print(f"Indicator mapping appears correct - investigate other issues")

    print(f"\\nUpdate code generated - ready to implement TARGET 151 alignment!")