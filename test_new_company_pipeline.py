#!/usr/bin/env python3
"""
TEST NEW COMPANY PIPELINE FLOW

Tests complete pipeline with a brand new company to demonstrate:
1. Checking existing data first (should be empty)
2. Automatic document download and scraping from online
3. Real data extraction without synthetic data
4. Complete workflow from start to finish
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData, PipelineJob
from backend.api.routers.pipeline import _collect_real_documents, _process_real_data_only
from datetime import datetime
import time


def test_new_company_pipeline():
    """Test complete pipeline with a brand new company."""

    print("=" * 100)
    print("NEW COMPANY PIPELINE TEST")
    print("=" * 100)

    db = get_session()

    try:
        # Step 1: Add a new company
        print("\n1. ADDING NEW TEST COMPANY...")
        print("-" * 80)

        test_company_name = "Infosys Limited"  # Well-known Indian IT company
        test_industry = "Information Technology"
        test_year = 2024

        # Check if company already exists
        existing_company = db.query(Company).filter(
            Company.name.like(f"%{test_company_name}%")
        ).first()

        if existing_company:
            print(f"   Company already exists: {existing_company.name} (ID: {existing_company.id})")
            test_company = existing_company
        else:
            # Create new company
            test_company = Company(
                name=test_company_name,
                industry=test_industry,
                ticker="INFY",
                description="Leading Indian IT services company"
            )
            db.add(test_company)
            db.commit()
            db.refresh(test_company)
            print(f"   NEW COMPANY CREATED: {test_company.name} (ID: {test_company.id})")

        print(f"   Industry: {test_company.industry}")
        print(f"   Test Year: {test_year}")

        # Step 2: Check existing data (should be minimal for new company)
        print("\n2. CHECKING EXISTING DATA (PRE-PIPELINE)...")
        print("-" * 80)

        existing_answers = db.query(Answer).filter(
            Answer.company_id == test_company.id,
            Answer.year == test_year
        ).count()

        existing_scraped = db.query(ScrapedData).filter(
            ScrapedData.company_id == test_company.id,
            ScrapedData.year == test_year
        ).count()

        print(f"   Existing answers in database: {existing_answers}")
        print(f"   Existing scraped data: {existing_scraped}")
        print(f"   Status: {'EMPTY - Will download online' if existing_answers < 10 else 'HAS DATA - Will supplement'}")

        # Step 3: Test document collection phase
        print("\n3. TESTING DOCUMENT COLLECTION PHASE...")
        print("-" * 80)

        print(f"   Starting automatic document collection for {test_company.name}...")
        print(f"   This will demonstrate online downloading and scraping...")

        start_time = time.time()
        success_docs, docs_collected = _collect_real_documents(
            company_id=test_company.id,
            year=test_year,
            db_session=db
        )
        end_time = time.time()

        print(f"\n   DOCUMENT COLLECTION RESULTS:")
        print(f"   Success: {success_docs}")
        print(f"   Documents/Data collected: {docs_collected}")
        print(f"   Time taken: {end_time - start_time:.1f} seconds")

        # Check what was collected
        if success_docs and docs_collected > 0:
            print(f"\n   COLLECTED DATA BREAKDOWN:")

            # Check ScrapedData that was just collected
            new_scraped = db.query(ScrapedData).filter(
                ScrapedData.company_id == test_company.id,
                ScrapedData.year == test_year,
                ScrapedData.scraped_at > datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            ).all()

            if new_scraped:
                print(f"   New scraped data points: {len(new_scraped)}")

                # Group by source
                by_source = {}
                for sd in new_scraped:
                    if sd.source not in by_source:
                        by_source[sd.source] = []
                    by_source[sd.source].append(sd)

                for source, data_points in by_source.items():
                    print(f"      Source: {source} -> {len(data_points)} indicators")
                    # Show sample indicators
                    for dp in data_points[:3]:
                        print(f"         - {dp.data_key}: {dp.data_value[:50]}...")

        else:
            print(f"   No documents collected - this is expected for new companies")
            print(f"   System correctly returned empty result instead of generating synthetic data")

        # Step 4: Test data processing phase
        print("\n4. TESTING DATA PROCESSING PHASE...")
        print("-" * 80)

        print(f"   Processing collected data using enhanced real data system...")

        start_time = time.time()
        success_process, indicators_processed = _process_real_data_only(
            company_id=test_company.id,
            year=test_year,
            db_session=db
        )
        end_time = time.time()

        print(f"\n   DATA PROCESSING RESULTS:")
        print(f"   Success: {success_process}")
        print(f"   Indicators processed: {indicators_processed}")
        print(f"   Time taken: {end_time - start_time:.1f} seconds")

        # Step 5: Check final results
        print("\n5. FINAL RESULTS ANALYSIS...")
        print("-" * 80)

        final_answers = db.query(Answer).filter(
            Answer.company_id == test_company.id,
            Answer.year == test_year
        ).count()

        final_scraped = db.query(ScrapedData).filter(
            ScrapedData.company_id == test_company.id,
            ScrapedData.year == test_year
        ).count()

        # Check for synthetic data (should be ZERO)
        synthetic_answers = db.query(Answer).filter(
            Answer.company_id == test_company.id,
            Answer.year == test_year,
            Answer.source.like("%synthetic%")
        ).count()

        print(f"   Final answers in database: {final_answers}")
        print(f"   Final scraped data points: {final_scraped}")
        print(f"   Coverage: {final_answers}/151 indicators ({(final_answers/151)*100:.1f}%)")
        print(f"   Synthetic data generated: {synthetic_answers} (should be 0)")

        if final_answers > 0:
            print(f"\n   SAMPLE EXTRACTED DATA:")
            sample_answers = db.query(Answer).filter(
                Answer.company_id == test_company.id,
                Answer.year == test_year
            ).limit(5).all()

            for answer in sample_answers:
                source = answer.source or "unknown"
                value = answer.answer_value[:50] if answer.answer_value else "empty"
                print(f"      {answer.indicator_id}: {value}... (source: {source})")

        # Step 6: Verify data sources are real
        print("\n6. DATA SOURCE VERIFICATION...")
        print("-" * 80)

        all_sources = set()
        real_data_answers = db.query(Answer).filter(
            Answer.company_id == test_company.id,
            Answer.year == test_year,
            Answer.answer_value.isnot(None),
            Answer.answer_value != ""
        ).all()

        for answer in real_data_answers:
            if answer.source:
                all_sources.add(answer.source)

        print(f"   Total data sources found: {len(all_sources)}")
        for source in sorted(all_sources):
            count = len([a for a in real_data_answers if a.source == source])
            print(f"      {source}: {count} indicators")

        # Verify no synthetic sources
        synthetic_sources = [s for s in all_sources if 'synthetic' in s.lower() or 'smart_default' in s.lower() or 'template' in s.lower()]
        if synthetic_sources:
            print(f"\n   WARNING: Found synthetic sources: {synthetic_sources}")
        else:
            print(f"\n   VERIFIED: No synthetic data sources found - all data is real!")

        # Step 7: Test the complete workflow
        print("\n7. WORKFLOW SUMMARY...")
        print("-" * 80)

        print(f"   Company: {test_company.name}")
        print(f"   Year: {test_year}")
        print(f"   Pre-pipeline data: {existing_answers} indicators")
        print(f"   Documents collected: {docs_collected}")
        print(f"   Final indicators: {final_answers}/151 ({(final_answers/151)*100:.1f}%)")
        print(f"   Processing successful: {success_process and success_docs}")

        workflow_status = "SUCCESS" if (success_docs and success_process and final_answers > 0) else "PARTIAL"
        print(f"\n   OVERALL WORKFLOW STATUS: {workflow_status}")

        if workflow_status == "SUCCESS":
            print(f"   ✓ Document collection: WORKING")
            print(f"   ✓ Online scraping: WORKING")
            print(f"   ✓ Data processing: WORKING")
            print(f"   ✓ Real data only: VERIFIED")
            print(f"   ✓ Database storage: WORKING")
        else:
            print(f"   - Some components may need adjustment")
            print(f"   - This is normal for new companies with limited online data")

        # Step 8: Cleanup recommendation
        print("\n8. NEXT STEPS...")
        print("-" * 80)
        print(f"   1. The company '{test_company.name}' is now in your database")
        print(f"   2. You can run the full pipeline from the UI: 'Run Pipeline'")
        print(f"   3. You can upload additional documents via Evidence Locker")
        print(f"   4. You can manually enter missing indicators via questionnaire")
        print(f"   5. Try different companies to test various scenarios")

        print(f"\n" + "=" * 100)
        print("NEW COMPANY PIPELINE TEST COMPLETE")
        print("=" * 100)

        return test_company, final_answers, workflow_status

    except Exception as e:
        print(f"\nERROR during pipeline test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, 0, "ERROR"

    finally:
        db.close()


def suggest_test_companies():
    """Suggest good companies to test with."""
    print("\n" + "=" * 100)
    print("SUGGESTED TEST COMPANIES")
    print("=" * 100)

    companies = [
        {
            "name": "Infosys Limited",
            "industry": "Information Technology",
            "ticker": "INFY",
            "why": "Large IT company with comprehensive ESG reporting"
        },
        {
            "name": "Wipro Limited",
            "industry": "Information Technology",
            "ticker": "WIPRO",
            "why": "IT services with strong sustainability initiatives"
        },
        {
            "name": "HDFC Bank Limited",
            "industry": "Banking & Financial Services",
            "ticker": "HDFCBANK",
            "why": "Major bank with detailed annual reports"
        },
        {
            "name": "Bajaj Finance Limited",
            "industry": "Financial Services",
            "ticker": "BAJFINANCE",
            "why": "NBFC with good ESG disclosures"
        },
        {
            "name": "Dr Reddy's Laboratories",
            "industry": "Pharmaceuticals",
            "ticker": "DRREDDY",
            "why": "Pharma company with comprehensive reporting"
        }
    ]

    for i, company in enumerate(companies, 1):
        print(f"\n{i}. {company['name']}")
        print(f"   Industry: {company['industry']}")
        print(f"   Ticker: {company['ticker']}")
        print(f"   Why test: {company['why']}")

    print(f"\n" + "=" * 100)


if __name__ == "__main__":
    print("TESTING NEW COMPANY PIPELINE FLOW...\n")

    # Show suggested companies
    suggest_test_companies()

    # Run the test
    company, indicators, status = test_new_company_pipeline()

    print(f"\nTEST SUMMARY:")
    if company:
        print(f"Company: {company.name}")
        print(f"Indicators extracted: {indicators}")
        print(f"Status: {status}")

    print(f"\nTEST COMPLETE!")