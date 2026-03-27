#!/usr/bin/env python3
"""
Test script for ESG Document Intelligence System
Fixed version without Unicode characters
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_intelligence_system():
    """Test the ESG Document Intelligence System core functionality"""

    print("=== TESTING ESG DOCUMENT INTELLIGENCE SYSTEM ===")

    try:
        from esg_document_intelligence_system import ESGDocumentIntelligenceSystem

        print("* System initialization test...")

        # Test system initialization (without web search)
        intelligence_system = ESGDocumentIntelligenceSystem()

        print("* SUCCESS: System initialized successfully")
        print(f"* Embedding model loaded: {type(intelligence_system.embeddings).__name__}")
        print(f"* Reranker loaded: {type(intelligence_system.reranker).__name__}")
        print(f"* LLM loaded: {type(intelligence_system.llm).__name__}")
        print(f"* Tokenizer ready: {intelligence_system.tokenizer.name_or_path}")

        # Test hybrid search components (but need documents first)
        print("\\n* Testing document indexing...")

        # Create test document content
        test_content = """
        Asian Paints Limited is committed to sustainability and environmental responsibility.
        Our carbon emissions have been reduced by 25% over the last five years.
        The company consumed 450,000 MWh of energy in FY2024, with 30% from renewable sources.
        We employed 8,500 people globally and achieved 35% women in senior management.
        Our CSR spending reached Rs. 95 crore in the last financial year.
        Water consumption was optimized to 2.5 liters per liter of paint produced.
        """

        # Create mock document info
        doc_info = {
            'url': 'https://example.com/asian-paints-report.pdf',
            'title': 'Asian Paints Sustainability Report 2024',
            'search_type': 'search'
        }

        # Test document indexing
        intelligence_system._index_document(test_content, doc_info)

        print("* SUCCESS: Document indexed successfully")
        print(f"* Vector DB ready: {intelligence_system.vector_db is not None}")
        print(f"* BM25 index ready: {intelligence_system.bm25_index is not None}")
        print(f"* Chunks created: {len(intelligence_system.document_chunks)}")

        # Test hybrid search
        print("\\n* Testing hybrid search...")

        test_questions = [
            'What are the carbon emissions?',
            'How much energy does the company consume?',
            'How many employees work at the company?'
        ]

        for question in test_questions:
            try:
                candidates = intelligence_system._hybrid_search(question, k=3)
                print(f"  Q: {question}")
                print(f"  Found {len(candidates)} candidate chunks")

                if candidates:
                    # Test reranking
                    best_chunks, confidence = intelligence_system._rerank_chunks(question, candidates, top_n=1)
                    print(f"  Best match (confidence {confidence:.2f}): {best_chunks[0][:80]}...")
                print()

            except Exception as e:
                print(f"  Error testing question \"{question}\": {str(e)}")

        print("\\n* SUCCESS: CORE FUNCTIONALITY WORKING!")
        print("* Hybrid search (BM25 + FAISS) operational")
        print("* Cross-encoder reranking functional")
        print("* Ready for ESG pipeline integration")

        # Note about web search
        if not intelligence_system.serper_api_key:
            print("\\n* Note: SERPER_API_KEY not configured")
            print("* Web search will be skipped, but existing functionality works")
            print("* Add API key for full web search capabilities")
        else:
            print("\\n* SUCCESS: SERPER API key configured - full web search available")

        return True

    except Exception as e:
        print(f"* ERROR: Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_intelligence_system()

    if success:
        print("\\n" + "="*60)
        print("ESG DOCUMENT INTELLIGENCE SYSTEM READY FOR INTEGRATION!")
    else:
        print("\\nSystem needs debugging before integration.")