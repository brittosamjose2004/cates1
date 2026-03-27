#!/usr/bin/env python3
"""
Test script for Scribd integration in ESG data extraction.
Tests the new Scribd fallback functionality added to ProvisionalWebScraper.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scraper.provisional_scraper import ProvisionalWebScraper

def test_scribd_search():
    """Test Scribd search functionality with real companies."""
    print("TESTING SCRIBD INTEGRATION")
    print("=" * 60)

    # Test with a well-known company that should have reports on Scribd
    test_cases = [
        ("Tata Consultancy Services", 2023),
        ("Asian Paints", 2023)
    ]

    for company_name, year in test_cases:
        print(f"\nTesting: {company_name} ({year})")
        print("-" * 40)

        scraper = ProvisionalWebScraper(company_name, year)

        # Test Scribd query building
        sample_indicator = {
            "indicator_id": "IMP-M01-I01",
            "indicator_name": "Company Identity & Registration",
            "question": "What is the company name and CIN number?"
        }

        # Test Scribd queries
        scribd_queries = scraper._build_scribd_queries(sample_indicator)
        print(f"Generated {len(scribd_queries)} Scribd queries:")
        for i, query in enumerate(scribd_queries):
            print(f"   {i+1}. {query}")

        # Test just the first query to avoid too many requests
        if scribd_queries:
            print(f"\nTesting search for: {scribd_queries[0]}")
            try:
                results = scraper._search_scribd(scribd_queries[0], max_results=2)
                print(f"Found {len(results)} Scribd documents")

                for j, doc in enumerate(results):
                    title = doc.get('title', 'No title')[:60]
                    url = doc.get('url', 'No URL')
                    snippet = doc.get('snippet', 'No snippet')[:80]
                    print(f"   {j+1}. {title}...")
                    print(f"      URL: {url}")
                    print(f"      Snippet: {snippet}...")
                    print()

            except Exception as e:
                print(f"Error testing Scribd search: {str(e)}")

def test_end_to_end():
    """Test the full provisional answer pipeline including Scribd."""
    print(f"\n\nTESTING END-TO-END WITH SCRIBD")
    print("=" * 60)

    scraper = ProvisionalWebScraper("Asian Paints", 2023)

    test_indicator = {
        "indicator_id": "IMP-M01-I01",
        "indicator_name": "Company Details",
        "question": "Company name, CIN, and registration details",
        "response_format": "Text",
    }

    print(f"Testing full pipeline for: {test_indicator['indicator_name']}")

    try:
        result = scraper.get_provisional_answer(test_indicator)
        if result:
            print("SUCCESS! Found provisional answer")
            print(f"Answer: {result.get('answer', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"Note: {result.get('note', 'N/A')}")

            # Check if it came from Scribd
            if result.get('source') == 'scribd_scraped':
                print("RESULT CAME FROM SCRIBD! Integration working!")
        else:
            print("No provisional answer found (all fallbacks failed)")

    except Exception as e:
        print(f"Error in end-to-end test: {str(e)}")

if __name__ == "__main__":
    print("Starting Scribd Integration Tests")
    print("Note: This tests the new Scribd fallback functionality")
    print("=" * 60)

    try:
        # Run tests
        test_scribd_search()
        test_end_to_end()

        print("\n\nTESTING COMPLETED")
        print("=" * 60)
        print("Scribd integration has been added as a fallback data source!")
        print("It will be used automatically when other sources don't have data.")

    except Exception as e:
        print(f"\n\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()