#!/usr/bin/env python3
"""
Test script for ESG Document Intelligence System integration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_intelligence_system():
    """Test the ESG Document Intelligence System"""

    print("=== TESTING ESG DOCUMENT INTELLIGENCE SYSTEM ===")

    try:
        # Test import
        from esg_document_intelligence_system_fixed import ESGDocumentIntelligenceSystem
        print("SUCCESS: Successfully imported ESGDocumentIntelligenceSystem")

        # Initialize system
        intelligence_system = ESGDocumentIntelligenceSystem()
        print("SUCCESS: Successfully initialized ESG Document Intelligence System")

        # Test with sample content
        sample_content = """
        Asian Paints sustainability and ESG performance report.
        Carbon emissions: 125,000 tonnes CO2 equivalent in 2024.
        Energy consumption: 450 GWh with 35% renewable energy.
        Workforce: 8,500 employees globally with 40% women in leadership.
        CSR expenditure: $12.5 million on community programs.
        Water usage: 2.8 million cubic meters with 30% recycled water.
        """

        doc_info = {
            'url': 'https://asianpaints.com/sustainability-report',
            'title': 'Asian Paints ESG Report 2024',
            'search_type': 'document'
        }

        # Index sample content
        intelligence_system._index_document(sample_content, doc_info)
        print("SUCCESS: Successfully indexed sample document")

        # Extract indicators using hybrid search
        import asyncio
        sample_indicators = asyncio.run(intelligence_system._extract_esg_indicators_hybrid(
            sample_content, "Asian Paints", 2024, doc_info
        ))

        print(f"SUCCESS: Successfully extracted {len(sample_indicators)} ESG indicators")

        # Display extracted indicators
        for i, indicator in enumerate(sample_indicators, 1):
            print(f"  {i}. {indicator['indicator_id']}: {indicator['data_value'][:100]}...")
            print(f"     Source: {indicator['source']}, Confidence: {indicator['confidence']:.2f}")

        print(f"\n=== TEST SUCCESS ===")
        print(f"ESG Document Intelligence System is ready for integration!")
        return True

    except Exception as e:
        print(f"ERROR: Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_intelligence_system()
    exit(0 if success else 1)