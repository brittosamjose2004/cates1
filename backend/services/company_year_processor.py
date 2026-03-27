"""
services/company_year_processor.py
Main orchestrator for complete company year-wise ESG data processing.

Handles end-to-end processing of:
- 21 ESG modules
- 151 indicators
- Multi-standard compliance (BRSR, CDP, EcoVadis, GRI)
- Year-wise data management
- Real-time monitoring integration
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass
import json

from backend.database.models import Company, QuestionnaireSession, Answer, ScrapedData, PipelineJob
from backend.database.db import get_session
from backend.processor.csv_loader import ImpactreeCSVLoader
from backend.processor.data_mapper import DataMapper
from backend.services.indicator_processor import IndicatorProcessor
from backend.services.module_processor import ModuleProcessor
from backend.services.scoring_engine import ScoringEngine


@dataclass
class ProcessingResult:
    """Result of company-year processing"""
    company_id: int
    year: int
    total_indicators: int
    processed_indicators: int
    failed_indicators: int
    modules_processed: List[str]
    processing_time_seconds: float
    final_score: Optional[float] = None
    module_scores: Dict[str, float] = None
    errors: List[str] = None


class CompanyYearProcessor:
    """
    Main orchestrator for complete ESG data processing per company per year.

    Coordinates:
    1. Data collection from all evidence sources
    2. Processing across 21 ESG modules
    3. Calculation of 151 indicators
    4. Multi-standard compliance mapping
    5. Scoring and rating generation
    6. Report generation
    """

    def __init__(self, company_id: str, year: int, standards: List[str] = None):
        """
        Initialize processor for a specific company and year.

        Args:
            company_id: Company identifier
            year: Year to process (e.g., 2024)
            standards: List of standards to comply with ['BRSR', 'CDP', 'EcoVadis', 'GRI']
        """
        self.company_id = int(company_id)
        self.year = year
        self.standards = standards or ['BRSR', 'CDP', 'EcoVadis', 'GRI']

        self.db: Optional[Session] = None
        self.company: Optional[Company] = None
        self.pipeline_job: Optional[PipelineJob] = None

        # Processing components
        self.indicator_processor = IndicatorProcessor()
        self.module_processor = ModuleProcessor()
        self.scoring_engine = ScoringEngine()

        # Processing state
        self.start_time: Optional[datetime] = None
        self.indicators_data: List[Dict[str, Any]] = []
        self.processing_results: Dict[str, Any] = {}


    def process_company_year(self,
                           force_refresh: bool = False,
                           include_real_time: bool = True,
                           trigger_scoring: bool = True) -> ProcessingResult:
        """
        Main entry point for complete company-year processing.

        Args:
            force_refresh: Re-process even if already completed
            include_real_time: Include real-time monitoring data
            trigger_scoring: Calculate final scores and ratings

        Returns:
            ProcessingResult with comprehensive stats and scores
        """
        self.start_time = datetime.utcnow()

        try:
            # 1. Initialize session and validate inputs
            self._initialize_session()

            # 2. Create or update pipeline job
            self._create_pipeline_job()

            # 3. Load all indicators for processing
            self._load_indicators()

            # 4. Process each module systematically
            module_results = self._process_all_modules()

            # 5. Calculate indicator values from multiple data sources
            indicator_results = self._process_all_indicators()

            # 6. Generate final scores and ratings
            scoring_results = None
            if trigger_scoring:
                scoring_results = self._calculate_scores()

            # 7. Update pipeline job status
            self._finalize_pipeline_job("COMPLETED")

            # 8. Generate processing result
            result = self._create_processing_result(
                module_results, indicator_results, scoring_results
            )

            return result

        except Exception as e:
            self._finalize_pipeline_job("ERROR", str(e))
            raise

        finally:
            if self.db:
                self.db.close()


    def _initialize_session(self):
        """Initialize database session and load company"""
        self.db = get_session()

        self.company = self.db.query(Company).filter_by(id=self.company_id).first()
        if not self.company:
            raise ValueError(f"Company {self.company_id} not found")


    def _create_pipeline_job(self):
        """Create or update pipeline job for tracking"""
        self.pipeline_job = PipelineJob(
            company_id=self.company_id,
            company_name=self.company.name,
            year=self.year,
            status="PROCESSING",
            data_sources=json.dumps(self.standards),
            triggered_by="CompanyYearProcessor",
            started_at=self.start_time
        )
        self.db.add(self.pipeline_job)
        self.db.commit()


    def _load_indicators(self):
        """Load all indicators for the specified standards"""
        if "ALL" in self.standards:
            self.indicators_data = ImpactreeCSVLoader.get_all_indicators()
        else:
            all_indicators = []
            for standard in self.standards:
                indicators = ImpactreeCSVLoader.get_indicators_by_standard(standard)
                all_indicators.extend(indicators)

            # Remove duplicates while preserving order
            seen = set()
            self.indicators_data = []
            for indicator in all_indicators:
                indicator_id = indicator.get('indicator_id')
                if indicator_id not in seen:
                    seen.add(indicator_id)
                    self.indicators_data.append(indicator)


    def _process_all_modules(self) -> Dict[str, Any]:
        """Process all 21 ESG modules systematically"""

        # Define the 21 modules from the data sources summary
        modules = [
            "General & Organizational Profile",
            "Sustainability Management & Reporting",
            "Governance & Ethics",
            "Risk & Opportunity Management",
            "GHG Emissions & Climate Change",
            "Energy",
            "Water & Effluents",
            "Waste & Materials",
            "Pollution & Emissions (Air Quality)",
            "Biodiversity & Land Use",
            "Supply Chain & Procurement",
            "Economic Performance",
            "Labor & Human Rights",
            "Occupational Health & Safety (OHS)",
            "Diversity, Equity & Inclusion",
            "Training & Skill Development",
            "Community & Social Impact",
            "Customer & Product Responsibility",
            "Legal & Environmental Compliance"
        ]

        module_results = {}
        processed_modules = []

        for module_name in modules:
            try:
                # Get indicators for this module
                module_indicators = [
                    ind for ind in self.indicators_data
                    if ind.get('module_name', '') == module_name
                ]

                if module_indicators:
                    print(f"Processing {module_name} ({len(module_indicators)} indicators)...")

                    # Process module-specific logic
                    result = self.module_processor.process_module(
                        company_id=self.company_id,
                        year=self.year,
                        module_name=module_name,
                        indicators=module_indicators,
                        db=self.db
                    )

                    module_results[module_name] = result
                    processed_modules.append(module_name)

            except Exception as e:
                print(f"Error processing {module_name}: {e}")
                module_results[module_name] = {"error": str(e)}

        return {
            "processed_modules": processed_modules,
            "module_results": module_results,
            "total_modules": len(modules),
            "processed_count": len(processed_modules)
        }


    def _process_all_indicators(self) -> Dict[str, Any]:
        """Process all 151 indicators with data from multiple sources"""

        processed_count = 0
        failed_count = 0
        indicator_results = {}

        for indicator in self.indicators_data:
            indicator_id = indicator.get('indicator_id')

            try:
                # Process individual indicator
                result = self.indicator_processor.process_indicator(
                    company_id=self.company_id,
                    year=self.year,
                    indicator=indicator,
                    db=self.db
                )

                indicator_results[indicator_id] = result
                processed_count += 1

            except Exception as e:
                print(f"Error processing indicator {indicator_id}: {e}")
                indicator_results[indicator_id] = {"error": str(e)}
                failed_count += 1

        return {
            "total_indicators": len(self.indicators_data),
            "processed_count": processed_count,
            "failed_count": failed_count,
            "indicator_results": indicator_results
        }


    def _calculate_scores(self) -> Dict[str, Any]:
        """Calculate final ESG scores and ratings"""

        return self.scoring_engine.calculate_company_scores(
            company_id=self.company_id,
            year=self.year,
            standards=self.standards,
            db=self.db
        )


    def _finalize_pipeline_job(self, status: str, error_msg: str = None):
        """Update pipeline job with final status"""
        if self.pipeline_job:
            self.pipeline_job.status = status
            self.pipeline_job.finished_at = datetime.utcnow()
            if error_msg:
                self.pipeline_job.error_msg = error_msg
            self.db.commit()


    def _create_processing_result(self,
                                module_results: Dict[str, Any],
                                indicator_results: Dict[str, Any],
                                scoring_results: Dict[str, Any] = None) -> ProcessingResult:
        """Create comprehensive processing result"""

        processing_time = (datetime.utcnow() - self.start_time).total_seconds()

        return ProcessingResult(
            company_id=self.company_id,
            year=self.year,
            total_indicators=indicator_results.get("total_indicators", 0),
            processed_indicators=indicator_results.get("processed_count", 0),
            failed_indicators=indicator_results.get("failed_count", 0),
            modules_processed=module_results.get("processed_modules", []),
            processing_time_seconds=processing_time,
            final_score=scoring_results.get("final_score") if scoring_results else None,
            module_scores=scoring_results.get("module_scores", {}) if scoring_results else {},
            errors=self._extract_errors(module_results, indicator_results)
        )


    def _extract_errors(self, module_results: Dict[str, Any],
                       indicator_results: Dict[str, Any]) -> List[str]:
        """Extract all errors from processing results"""
        errors = []

        # Module errors
        for module, result in module_results.get("module_results", {}).items():
            if "error" in result:
                errors.append(f"Module {module}: {result['error']}")

        # Indicator errors
        for indicator_id, result in indicator_results.get("indicator_results", {}).items():
            if "error" in result:
                errors.append(f"Indicator {indicator_id}: {result['error']}")

        return errors


# ── Standalone Functions ──────────────────────────────────────────────────

def process_company_year(company_id: str, year: int, **kwargs) -> ProcessingResult:
    """
    Convenience function for processing a single company-year.

    Usage:
        result = process_company_year("14", 2024)
        print(f"Processed {result.processed_indicators}/{result.total_indicators} indicators")
        print(f"Final score: {result.final_score}")
    """
    processor = CompanyYearProcessor(company_id, year)
    return processor.process_company_year(**kwargs)


def process_multiple_companies(company_years: List[tuple], **kwargs) -> List[ProcessingResult]:
    """
    Process multiple company-year combinations.

    Args:
        company_years: List of (company_id, year) tuples

    Returns:
        List of ProcessingResult objects
    """
    results = []

    for company_id, year in company_years:
        try:
            result = process_company_year(company_id, year, **kwargs)
            results.append(result)
        except Exception as e:
            print(f"Failed to process company {company_id} year {year}: {e}")
            continue

    return results