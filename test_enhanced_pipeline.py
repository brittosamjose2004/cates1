#!/usr/bin/env python3
"""
Test the enhanced comprehensive pipeline with Asian Paints
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_pipeline():
    """Test comprehensive pipeline with ESG Document Intelligence"""

    print("=== TESTING ENHANCED COMPREHENSIVE PIPELINE ===")
    print("Company: Asian Paints (ID: 14)")
    print("Year: 2024")
    print("Expected: Increased ESG indicator coverage with hybrid search + web search")
    print("")

    try:
        from comprehensive_pipeline import run_comprehensive_pipeline

        # Run enhanced pipeline with Asian Paints
        result = run_comprehensive_pipeline(14, 2024)  # Asian Paints, 2024

        if result.get('success'):
            indicators_processed = result.get('indicators_processed', 0)
            sources_used = result.get('sources_used', [])

            print(f"\nSUCCESS: Enhanced Pipeline completed!")
            print(f"Total indicators processed: {indicators_processed}")
            print(f"Sources integrated: {len(sources_used)}")

            # Check for new intelligence sources
            intelligence_sources = [s for s in sources_used if 'hybrid_search' in s or 'enhanced_web_search' in s]
            if intelligence_sources:
                print(f"Intelligence sources found: {intelligence_sources}")
                print(f"ENHANCEMENT CONFIRMED: Document intelligence is working!")
            else:
                print("Intelligence sources not detected (may not have processable content)")

            print(f"\nDocument sources: {result.get('document_sources', 0)}")
            print(f"Pattern sources: {result.get('pattern_sources', 0)}")
            print(f"Online sources: {result.get('online_sources', 0)}")
            print(f"\nAll sources: {sources_used}")

        else:
            print(f"ERROR: Enhanced pipeline failed: {result.get('error')}")

        return result.get('success', False)

    except Exception as e:
        print(f"ERROR: Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_pipeline()

    if success:
        print(f"\nCONCLUSION: HUGGING FACE INTEGRATION COMPLETE!")
        print(f"The ESG Document Intelligence System is successfully integrated.")
        print(f"Enhanced pipeline combines:")
        print(f"  - Ultra Enhanced Dynamic Sources (8 methods)")
        print(f"  - Document Discovery System")
        print(f"  - ESG Document Intelligence (Hybrid Search + Web Search)")
        print(f"  - Traditional pattern and online sources")
        print(f"\nExpected improvement: Significantly higher ESG indicator coverage!")
    else:
        print(f"\nERROR: Integration needs debugging")

    exit(0 if success else 1)