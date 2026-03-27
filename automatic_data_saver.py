#!/usr/bin/env python3
"""
AUTOMATIC DATA SOURCES SAVER
Automatically save data sources every time pipeline runs or data is processed
Integrates with the existing pipeline system for seamless automatic saving
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
from datetime import datetime
from typing import Dict, Optional
from data_source_tracker import DataSourceTracker

class AutomaticDataSourceSaver:
    """Automatically save data sources during pipeline processing"""

    def __init__(self):
        self.tracker = DataSourceTracker()
        self.auto_save_enabled = True
        self.last_save_log = {}

    def auto_save_data_sources(self, company_id: int, year: int, context: str = "pipeline") -> Optional[Dict]:
        """
        Automatically save data sources for a company-year combination
        Called automatically during pipeline processing

        Args:
            company_id: Company ID
            year: Year being processed
            context: Context of the save (pipeline, manual, etc.)

        Returns:
            Summary dict if successful, None if failed/disabled
        """
        if not self.auto_save_enabled:
            return None

        try:
            # Get data sources summary
            summary = self.tracker.get_company_year_data_sources(company_id, year)

            if 'error' in summary:
                print(f"[AUTO-SAVE] Skipping save for company {company_id} year {year}: {summary['error']}")
                return None

            # Add auto-save metadata
            summary['auto_save_context'] = context
            summary['auto_save_timestamp'] = datetime.now().isoformat()

            # Save the report
            report_path = self.tracker.save_data_sources_report(company_id, year, summary)

            # Log the auto-save
            save_key = f"{company_id}_{year}"
            self.last_save_log[save_key] = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'indicators': summary['total_indicators'],
                'sources': summary['total_sources'],
                'coverage': summary['coverage_analysis']['target_151_coverage'],
                'report_path': report_path
            }

            print(f"[AUTO-SAVE] Saved data sources for {summary['company_name']} {year}")
            print(f"[AUTO-SAVE] {summary['total_indicators']} indicators from {summary['total_sources']} sources -> {Path(report_path).name}")

            return summary

        except Exception as e:
            print(f"[AUTO-SAVE] Failed to save data sources for company {company_id} year {year}: {str(e)}")
            return None

    def get_auto_save_status(self) -> Dict:
        """Get status of automatic saving"""
        return {
            'enabled': self.auto_save_enabled,
            'total_auto_saves': len(self.last_save_log),
            'recent_saves': list(self.last_save_log.values())[-5:],  # Last 5 saves
            'tracking_directory': str(self.tracker.data_sources_dir)
        }

    def enable_auto_save(self):
        """Enable automatic saving"""
        self.auto_save_enabled = True
        print("[AUTO-SAVE] Automatic data source saving ENABLED")

    def disable_auto_save(self):
        """Disable automatic saving"""
        self.auto_save_enabled = False
        print("[AUTO-SAVE] Automatic data source saving DISABLED")

# Create global instance for pipeline integration
auto_saver = AutomaticDataSourceSaver()

def pipeline_auto_save_data_sources(company_id: int, year: int) -> Optional[Dict]:
    """
    Function to be called by pipeline for automatic data source saving
    This is the main integration point for the pipeline
    """
    return auto_saver.auto_save_data_sources(company_id, year, context="pipeline_run")

def manual_auto_save_data_sources(company_id: int, year: int) -> Optional[Dict]:
    """
    Function for manual/API triggered automatic saving
    """
    return auto_saver.auto_save_data_sources(company_id, year, context="manual_trigger")

if __name__ == "__main__":
    # Test automatic saving
    print("[TEST] Automatic Data Sources Saver")
    print("=" * 80)

    # Test with JSW Steel 2023
    print("Testing automatic save for JSW Steel 2023...")
    result = pipeline_auto_save_data_sources(44, 2023)

    if result:
        print(f"SUCCESS Auto-save successful!")
        print(f"Company: {result['company_name']}")
        print(f"Year: {result['year']}")
        print(f"Indicators: {result['total_indicators']}")
        print(f"Coverage: {result['coverage_analysis']['target_151_coverage']}")
    else:
        print("ERROR Auto-save failed")

    # Show auto-save status
    print(f"\n[AUTO-SAVE STATUS]")
    status = auto_saver.get_auto_save_status()
    print(f"Enabled: {status['enabled']}")
    print(f"Total auto-saves: {status['total_auto_saves']}")
    print(f"Tracking directory: {status['tracking_directory']}")

    if status['recent_saves']:
        print(f"Recent saves:")
        for save in status['recent_saves']:
            print(f"  {save['timestamp']}: {save['indicators']} indicators, {save['coverage']} coverage")