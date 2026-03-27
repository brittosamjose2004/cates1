#!/usr/bin/env python3
"""
Verify the CLI pipeline results for Infosys Limited
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData

def verify_pipeline_results():
    """Verify that the CLI pipeline stored data correctly"""

    print("=" * 80)
    print("VERIFYING CLI PIPELINE RESULTS")
    print("=" * 80)

    db = get_session()

    try:
        # Find Infosys Limited
        company = db.query(Company).filter_by(name="Infosys Limited").first()
        if not company:
            print("ERROR: Infosys Limited not found!")
            return

        print(f"Company: {company.name} (ID: {company.id})")
        print(f"Industry: {company.industry}")

        # Check answers table
        answers = db.query(Answer).filter(
            Answer.company_id == company.id,
            Answer.year == 2024
        ).all()

        print(f"\nAnswers in database: {len(answers)}")

        if answers:
            # Group by source
            by_source = {}
            for answer in answers:
                source = answer.source or "unknown"
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(answer)

            print(f"\nData sources:")
            for source, data in by_source.items():
                print(f"   {source}: {len(data)} indicators")

            print(f"\nSample indicators:")
            for answer in answers[:10]:
                source = answer.source or "unknown"
                value = answer.answer_value[:50] if answer.answer_value else "empty"
                print(f"   {answer.indicator_id}: {value}... (source: {source})")

        # Check scraped data
        scraped = db.query(ScrapedData).filter(
            ScrapedData.company_id == company.id,
            ScrapedData.year == 2024
        ).all()

        print(f"\nScraped data points: {len(scraped)}")

        if scraped:
            by_source = {}
            for sd in scraped:
                if sd.source not in by_source:
                    by_source[sd.source] = []
                by_source[sd.source].append(sd)

            print(f"\nScraped data sources:")
            for source, data in by_source.items():
                print(f"   {source}: {len(data)} data points")

        # Summary
        total_data = len(answers) + len(scraped)
        print(f"\n" + "=" * 80)
        print(f"SUMMARY")
        print(f"=" * 80)
        print(f"Company: {company.name}")
        print(f"Total indicators in answers table: {len(answers)}")
        print(f"Total scraped data points: {len(scraped)}")
        print(f"Total data points: {total_data}")
        print(f"CLI processing: {'SUCCESS' if len(answers) > 0 else 'PARTIAL'}")
        print(f"Ready for frontend test: {'YES' if len(answers) > 100 else 'CHECK'}")

    finally:
        db.close()

if __name__ == "__main__":
    verify_pipeline_results()