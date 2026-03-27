#!/usr/bin/env python3
"""
DATA SOURCE TRACKER AND SAVER
Track and save all data sources and scraping methods used for each company-year combination
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backend.database.db import get_session
from backend.database.models import Company, Answer, ScrapedData

class DataSourceTracker:
    """Track and save data sources used for each company-year combination"""

    def __init__(self):
        self.data_sources_dir = Path("data_sources_tracking")
        self.data_sources_dir.mkdir(exist_ok=True)

    def get_company_year_data_sources(self, company_id: int, year: int) -> Dict:
        """
        Get comprehensive data sources information for a specific company-year combination
        Returns detailed breakdown of all data sources and what they provided
        """
        db = get_session()
        try:
            company = db.query(Company).filter_by(id=company_id).first()
            if not company:
                return {"error": f"Company {company_id} not found"}

            print(f"[DATA SOURCE ANALYSIS] {company.name} - Year {year}")
            print("=" * 80)

            # 1. Scraped Data Sources
            scraped_data = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year
            ).all()

            sources_breakdown = {}
            indicators_by_source = {}
            total_indicators = 0

            for data in scraped_data:
                source = data.source if hasattr(data, 'source') else 'unknown'
                indicator_id = data.data_key if hasattr(data, 'data_key') else 'unknown'
                value = data.data_value if hasattr(data, 'data_value') else None

                if source not in sources_breakdown:
                    sources_breakdown[source] = {
                        'type': 'scraped',
                        'indicator_count': 0,
                        'indicators': [],
                        'sample_values': []
                    }

                if indicator_id.startswith('IMP-M') and value:
                    sources_breakdown[source]['indicator_count'] += 1
                    sources_breakdown[source]['indicators'].append(indicator_id)

                    # Store sample values (first 3)
                    if len(sources_breakdown[source]['sample_values']) < 3:
                        sources_breakdown[source]['sample_values'].append({
                            'indicator': indicator_id,
                            'value': str(value)[:100]  # Truncate for display
                        })
                    total_indicators += 1

            # 2. Manual Data Sources
            manual_data = db.query(Answer).filter_by(
                company_id=company_id,
                year=year
            ).all()

            manual_count = 0
            manual_indicators = []
            for answer in manual_data:
                if hasattr(answer, 'indicator_id') and hasattr(answer, 'answer_value'):
                    if answer.indicator_id and answer.answer_value:
                        manual_count += 1
                        manual_indicators.append({
                            'indicator': answer.indicator_id,
                            'value': str(answer.answer_value)[:100]
                        })

            if manual_count > 0:
                sources_breakdown['manual_input'] = {
                    'type': 'manual',
                    'indicator_count': manual_count,
                    'indicators': [item['indicator'] for item in manual_indicators],
                    'sample_values': manual_indicators[:3]
                }

            # 3. Determine source types and methods
            source_methods = self._classify_sources(sources_breakdown.keys())

            # 4. Create comprehensive summary
            summary = {
                'company_id': company_id,
                'company_name': company.name,
                'year': year,
                'analysis_date': datetime.now().isoformat(),
                'total_indicators': total_indicators + manual_count,
                'total_sources': len(sources_breakdown),
                'source_breakdown': sources_breakdown,
                'source_methods': source_methods,
                'coverage_analysis': self._analyze_coverage(sources_breakdown)
            }

            return summary

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
        finally:
            db.close()

    def _classify_sources(self, source_names: List[str]) -> Dict:
        """Classify data sources by collection method"""
        methods = {
            'comprehensive_extraction': [],
            'web_scraping': [],
            'document_upload': [],
            'manual_entry': [],
            'api_collection': [],
            'unknown': []
        }

        for source in source_names:
            source_lower = source.lower()

            if 'comprehensive' in source_lower or 'extraction' in source_lower:
                methods['comprehensive_extraction'].append(source)
            elif 'web' in source_lower or 'website' in source_lower or 'scraping' in source_lower:
                methods['web_scraping'].append(source)
            elif 'upload' in source_lower or 'pdf' in source_lower or 'document' in source_lower:
                methods['document_upload'].append(source)
            elif 'manual' in source_lower or 'input' in source_lower:
                methods['manual_entry'].append(source)
            elif 'api' in source_lower or 'nse' in source_lower:
                methods['api_collection'].append(source)
            else:
                methods['unknown'].append(source)

        return methods

    def _analyze_coverage(self, sources_breakdown: Dict) -> Dict:
        """Analyze coverage quality and completeness"""
        total_indicators = sum(source['indicator_count'] for source in sources_breakdown.values())

        # Calculate coverage by type
        scraped_indicators = sum(
            source['indicator_count']
            for source in sources_breakdown.values()
            if source['type'] == 'scraped'
        )

        manual_indicators = sum(
            source['indicator_count']
            for source in sources_breakdown.values()
            if source['type'] == 'manual'
        )

        coverage = {
            'total_indicators': total_indicators,
            'scraped_indicators': scraped_indicators,
            'manual_indicators': manual_indicators,
            'target_151_coverage': f"{(total_indicators/151)*100:.1f}%" if total_indicators > 0 else "0%",
            'data_quality': 'EXCELLENT' if total_indicators > 140 else 'GOOD' if total_indicators > 100 else 'PARTIAL'
        }

        return coverage

    def save_data_sources_report(self, company_id: int, year: int, summary: Dict) -> str:
        """Save detailed data sources report to file"""
        # Create filename
        company_name = summary.get('company_name', f'company_{company_id}').replace(' ', '_').replace('.', '')
        filename = f"{company_name}_{year}_data_sources.json"
        filepath = self.data_sources_dir / filename

        # Save detailed report
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Also create human-readable summary
        summary_filename = f"{company_name}_{year}_summary.txt"
        summary_filepath = self.data_sources_dir / summary_filename

        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write(f"DATA SOURCES REPORT\n")
            f.write(f"Company: {summary['company_name']} (ID: {company_id})\n")
            f.write(f"Year: {year}\n")
            f.write(f"Analysis Date: {summary['analysis_date']}\n")
            f.write(f"="*60 + "\n\n")

            f.write(f"SUMMARY:\n")
            f.write(f"Total Indicators: {summary['total_indicators']}\n")
            f.write(f"Total Sources: {summary['total_sources']}\n")
            f.write(f"Target 151 Coverage: {summary['coverage_analysis']['target_151_coverage']}\n")
            f.write(f"Data Quality: {summary['coverage_analysis']['data_quality']}\n\n")

            f.write(f"SOURCES BREAKDOWN:\n")
            for source_name, source_data in summary['source_breakdown'].items():
                f.write(f"\n{source_name}:\n")
                f.write(f"  Type: {source_data['type']}\n")
                f.write(f"  Indicators: {source_data['indicator_count']}\n")
                f.write(f"  Sample Data:\n")
                for sample in source_data['sample_values'][:2]:
                    f.write(f"    {sample['indicator']}: {sample['value'][:50]}...\n")

            f.write(f"\nSOURCE METHODS:\n")
            for method, sources in summary['source_methods'].items():
                if sources:
                    f.write(f"  {method.upper()}: {', '.join(sources)}\n")

        return str(filepath)

    def display_data_sources_summary(self, company_id: int, year: int):
        """Display comprehensive data sources summary"""
        summary = self.get_company_year_data_sources(company_id, year)

        if 'error' in summary:
            print(f"[ERROR] {summary['error']}")
            return None

        print(f"\n[COMPREHENSIVE DATA SOURCES] {summary['company_name']} - {year}")
        print("=" * 80)

        # Overall summary
        coverage = summary['coverage_analysis']
        print(f"Total Indicators Found: {summary['total_indicators']}")
        print(f"Target 151 Coverage: {coverage['target_151_coverage']}")
        print(f"Data Quality: {coverage['data_quality']}")
        print(f"Total Sources Used: {summary['total_sources']}")

        # Sources breakdown
        print(f"\n[DETAILED SOURCES BREAKDOWN]")
        print("-" * 60)

        for source_name, source_data in summary['source_breakdown'].items():
            print(f"\n{source_name.upper()}:")
            print(f"  Type: {source_data['type'].upper()}")
            print(f"  Indicators: {source_data['indicator_count']}")

            if source_data['sample_values']:
                print(f"  Sample Data:")
                for sample in source_data['sample_values'][:2]:
                    print(f"    {sample['indicator']}: {sample['value'][:60]}...")

        # Methods used
        print(f"\n[SCRAPING/COLLECTION METHODS]")
        print("-" * 60)
        for method, sources in summary['source_methods'].items():
            if sources:
                print(f"{method.upper().replace('_', ' ')}: {len(sources)} sources")
                for source in sources[:3]:  # Show first 3
                    print(f"  - {source}")

        # Save report
        report_path = self.save_data_sources_report(company_id, year, summary)
        print(f"\n[SAVED] Detailed report saved to: {report_path}")

        return summary

def main():
    """Main function for testing data source tracking"""
    tracker = DataSourceTracker()

    # Test with JSW Steel 2023
    print("[DATA SOURCE TRACKER] Testing with JSW Steel Limited 2023")
    print("=" * 100)

    summary = tracker.display_data_sources_summary(44, 2023)

    if summary:
        print(f"\n[SUCCESS] Data source analysis complete!")
        print(f"Found {summary['total_indicators']} indicators from {summary['total_sources']} sources")
    else:
        print(f"[FAILED] Could not analyze data sources")

if __name__ == "__main__":
    main()