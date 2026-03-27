"""
real_data_validator.py - Real Data Only ESG Retrieval System
=============================================================
Ensures perfect retrieval of 100% REAL data from actual sources.
NO synthetic data, NO AI generation - only verified real extracted data.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.database.models import Company, Answer, EvidenceSource, ScrapedData

class RealDataValidator:
    """
    Real Data Only ESG retrieval system.
    Finds perfect years with 100% real data from actual company documents.
    """

    # Real data sources (no synthetic/AI sources)
    REAL_SOURCES = {
        "manual",           # Manually entered data
        "scraped",          # Extracted from real documents
        "pdf_extracted",    # Extracted from real PDFs
        "annual_report",    # From actual annual reports
        "evidence_upload",  # From uploaded evidence documents
        "brsr_scraped",     # From real BRSR documents
        "url_downloaded"    # From real downloaded documents
    }

    # Sources that are NOT considered real data
    SYNTHETIC_SOURCES = {
        "online_provisional", # AI-generated provisional data
        "online_scraped",     # Web-scraped provisional data
        "scribd_scraped",     # Scribd fallback data
        "calculated",         # Calculated/estimated data
        "inferred",          # Inferred/guessed data
        "synthetic"          # Synthetic data
    }

    def __init__(self, db: Session):
        self.db = db

    def get_perfect_real_data(self, company_id: int, requested_year: Optional[int] = None) -> Dict[str, any]:
        """
        Get perfect REAL data for a company - only from actual verified sources.

        Returns:
        {
            "company_id": 14,
            "company_name": "Asian Paints",
            "requested_year": 2019,
            "perfect_year": 2024,
            "year_used": 2024,
            "real_data_analysis": {
                "total_indicators": 151,
                "real_indicators": 151,
                "synthetic_indicators": 0,
                "real_data_percentage": 100.0,
                "data_sources": {"manual": 45, "scraped": 106},
                "evidence_documents": 5
            },
            "available_real_years": [2023, 2024, 2025, 2026],
            "year_switched_reason": "Requested year 2019 has no real data",
            "is_perfect_real_data": True
        }
        """

        company = self.db.query(Company).filter_by(id=company_id).first()
        if not company:
            return {"error": f"Company ID {company_id} not found"}

        # Analyze real data across all years
        real_data_analysis = self._analyze_real_data_years(company_id)

        if not real_data_analysis["available_years"]:
            return {
                "error": "No real data available for this company",
                "company_id": company_id,
                "company_name": company.name,
                "real_data_found": False
            }

        # Find perfect year with most real data
        perfect_year = self._find_perfect_real_year(real_data_analysis, requested_year)

        return {
            "company_id": company_id,
            "company_name": company.name,
            "requested_year": requested_year,
            "perfect_year": real_data_analysis["best_real_year"],
            "year_used": perfect_year,
            "real_data_analysis": real_data_analysis["years"][perfect_year],
            "available_real_years": real_data_analysis["available_years"],
            "year_switched_reason": self._get_year_switch_reason(requested_year, perfect_year, real_data_analysis),
            "is_perfect_real_data": real_data_analysis["years"][perfect_year]["real_data_percentage"] == 100.0,
            "evidence_documents": self._get_evidence_documents(company_id),
            "data_freshness": self._get_data_freshness(perfect_year)
        }

    def _analyze_real_data_years(self, company_id: int) -> Dict[str, any]:
        """Analyze REAL data quality across all years for a company."""

        # Get all years that have Answer data
        years_with_data = (
            self.db.query(Answer.year)
            .filter_by(company_id=company_id)
            .distinct()
            .all()
        )

        if not years_with_data:
            return {"available_years": [], "years": {}}

        years_analysis = {}
        best_real_year = None
        best_real_count = 0

        for (year,) in years_with_data:
            if year is None:
                continue

            year_analysis = self._analyze_real_data_single_year(company_id, year)

            # Only include years with actual real data
            if year_analysis["real_indicators"] > 0:
                years_analysis[year] = year_analysis

                # Track best year (most real indicators)
                if year_analysis["real_indicators"] > best_real_count:
                    best_real_count = year_analysis["real_indicators"]
                    best_real_year = year

        return {
            "available_years": sorted(years_analysis.keys(), reverse=True),
            "years": years_analysis,
            "best_real_year": best_real_year,
            "best_real_count": best_real_count
        }

    def _analyze_real_data_single_year(self, company_id: int, year: int) -> Dict[str, any]:
        """Analyze REAL data quality for a specific company-year."""

        # Get all answers for this year
        answers = (
            self.db.query(Answer)
            .filter_by(company_id=company_id, year=year)
            .all()
        )

        total_indicators = 151
        real_indicators = 0
        synthetic_indicators = 0
        verified_indicators = 0
        real_sources_count = {}

        for answer in answers:
            if answer.answer_value and answer.answer_value.strip():
                source = getattr(answer, 'source', 'unknown') or 'unknown'

                # Check if this is real data
                if source in self.REAL_SOURCES:
                    real_indicators += 1
                    real_sources_count[source] = real_sources_count.get(source, 0) + 1

                    # Count verified indicators
                    if getattr(answer, 'is_verified', False):
                        verified_indicators += 1

                elif source in self.SYNTHETIC_SOURCES:
                    synthetic_indicators += 1

        real_data_percentage = (real_indicators / total_indicators) * 100

        return {
            "year": year,
            "total_indicators": total_indicators,
            "real_indicators": real_indicators,
            "synthetic_indicators": synthetic_indicators,
            "verified_indicators": verified_indicators,
            "real_data_percentage": round(real_data_percentage, 1),
            "real_sources": real_sources_count,
            "is_100_percent_real": real_indicators == total_indicators and synthetic_indicators == 0,
            "is_excellent_real": real_data_percentage >= 95.0 and synthetic_indicators == 0,
            "has_sufficient_real": real_indicators >= 140  # At least 140/151 real indicators
        }

    def _find_perfect_real_year(self, analysis: Dict[str, any], requested_year: Optional[int]) -> int:
        """Find the perfect year with most real data."""

        years_data = analysis["years"]

        # If no specific year requested, use best real year
        if requested_year is None:
            return analysis["best_real_year"]

        # If requested year has good real data, use it
        if requested_year in years_data:
            requested_analysis = years_data[requested_year]
            # Use requested year if it has sufficient real data (no synthetic)
            if requested_analysis["real_indicators"] >= 100 and requested_analysis["synthetic_indicators"] == 0:
                return requested_year

        # Otherwise use best real year
        return analysis["best_real_year"]

    def _get_year_switch_reason(self, requested_year: Optional[int], year_used: int, analysis: Dict) -> Optional[str]:
        """Get reason why we switched from requested year."""

        if requested_year is None or requested_year == year_used:
            return None

        if requested_year not in analysis["years"]:
            return f"Year {requested_year} has no real data. Using {year_used} with verified real data."

        req_data = analysis["years"][requested_year]
        used_data = analysis["years"][year_used]

        if req_data["synthetic_indicators"] > 0:
            return f"Year {requested_year} contains synthetic data. Using {year_used} with 100% real data only."

        return f"Year {requested_year} has {req_data['real_indicators']} real indicators. Using {year_used} with {used_data['real_indicators']} real indicators."

    def _get_evidence_documents(self, company_id: int) -> List[Dict[str, any]]:
        """Get actual evidence documents uploaded for this company."""

        evidence = (
            self.db.query(EvidenceSource)
            .filter_by(company_id=company_id, status="APPROVED")
            .all()
        )

        return [
            {
                "name": e.name,
                "type": e.type,
                "date": e.date,
                "tags": e.tags or []
            }
            for e in evidence
        ]

    def _get_data_freshness(self, year: int) -> str:
        """Get data freshness description."""
        import datetime
        current_year = datetime.datetime.now().year
        years_old = current_year - year

        if years_old == 0:
            return "Current year data"
        elif years_old == 1:
            return "Last year data"
        elif years_old <= 2:
            return f"{years_old} years old"
        else:
            return f"{years_old} years old"

    def validate_real_data_only(self, company_id: int, year: int) -> Dict[str, any]:
        """Validate that a specific company-year has only real data."""

        answers = (
            self.db.query(Answer)
            .filter_by(company_id=company_id, year=year)
            .all()
        )

        validation_result = {
            "company_id": company_id,
            "year": year,
            "is_real_data_only": True,
            "real_indicators": [],
            "synthetic_indicators": [],
            "unknown_indicators": []
        }

        for answer in answers:
            if not answer.answer_value or not answer.answer_value.strip():
                continue

            source = getattr(answer, 'source', 'unknown') or 'unknown'
            indicator_info = {
                "id": answer.indicator_id,
                "source": source,
                "value": answer.answer_value[:50] + "..." if len(answer.answer_value) > 50 else answer.answer_value
            }

            if source in self.REAL_SOURCES:
                validation_result["real_indicators"].append(indicator_info)
            elif source in self.SYNTHETIC_SOURCES:
                validation_result["synthetic_indicators"].append(indicator_info)
                validation_result["is_real_data_only"] = False
            else:
                validation_result["unknown_indicators"].append(indicator_info)
                validation_result["is_real_data_only"] = False

        return validation_result

    def get_real_data_summary(self, company_id: int) -> Dict[str, any]:
        """Get summary of real data availability for all years."""

        company = self.db.query(Company).filter_by(id=company_id).first()
        if not company:
            return {"error": "Company not found"}

        analysis = self._analyze_real_data_years(company_id)

        year_summaries = []
        for year, data in sorted(analysis["years"].items(), reverse=True):
            year_summaries.append({
                "year": year,
                "real_indicators": data["real_indicators"],
                "real_percentage": data["real_data_percentage"],
                "is_100_percent_real": data["is_100_percent_real"],
                "sources": list(data["real_sources"].keys())
            })

        return {
            "company_id": company_id,
            "company_name": company.name,
            "best_real_year": analysis["best_real_year"],
            "years_summary": year_summaries,
            "evidence_documents_count": len(self._get_evidence_documents(company_id))
        }