"""
smart_year_resolver.py - Intelligent Year Selection for ESG Data
===============================================================
Ensures perfect data retrieval by automatically finding the best year with complete data.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.database.models import Company, Answer

class SmartYearResolver:
    """
    Intelligent year resolution for ESG data retrieval.
    Automatically finds the best year with complete data for any company.
    """

    def __init__(self, db: Session):
        self.db = db
        self._year_cache: Dict[int, Dict[str, any]] = {}  # company_id -> year analysis

    def get_perfect_year_data(self, company_id: int, requested_year: Optional[int] = None) -> Dict[str, any]:
        """
        Get the perfect ESG data for a company, with intelligent year selection.

        Returns:
        {
            "recommended_year": 2024,
            "requested_year": 2019,
            "year_used": 2024,
            "data_quality": {
                "completeness_percentage": 100.0,
                "indicators_with_data": 151,
                "total_indicators": 151,
                "confidence_score": 0.92
            },
            "available_years": [2023, 2024, 2025, 2026],
            "year_quality_analysis": {...},
            "fallback_reason": "Requested year has insufficient data",
            "perfect_data": True
        }
        """

        # Get company info
        company = self.db.query(Company).filter_by(id=company_id).first()
        if not company:
            raise ValueError(f"Company ID {company_id} not found")

        # Analyze all available years
        year_analysis = self._analyze_company_years(company_id)

        if not year_analysis:
            return {
                "error": "No data available for this company",
                "company_id": company_id,
                "company_name": company.name,
                "available_years": [],
                "recommended_year": None
            }

        # Find the perfect year to use
        best_year = self._select_perfect_year(year_analysis, requested_year)

        return {
            "company_id": company_id,
            "company_name": company.name,
            "requested_year": requested_year,
            "year_used": best_year,
            "recommended_year": year_analysis["best_year"],
            "data_quality": year_analysis["years"][best_year],
            "available_years": sorted(year_analysis["years"].keys(), reverse=True),
            "year_quality_analysis": year_analysis["years"],
            "fallback_reason": self._get_fallback_reason(requested_year, best_year, year_analysis),
            "perfect_data": year_analysis["years"][best_year]["completeness_percentage"] >= 95.0,
            "data_freshness": self._calculate_data_freshness(best_year),
        }

    def _analyze_company_years(self, company_id: int) -> Dict[str, any]:
        """Analyze data quality for all available years for a company."""

        if company_id in self._year_cache:
            return self._year_cache[company_id]

        # Get all years with data
        answer_years = (
            self.db.query(Answer.year)
            .filter_by(company_id=company_id)
            .distinct()
            .all()
        )

        if not answer_years:
            return {}

        years_analysis = {}
        best_year_score = 0
        best_year = None

        for (year,) in answer_years:
            if year is None:
                continue

            analysis = self._analyze_single_year(company_id, year)
            years_analysis[year] = analysis

            # Calculate overall score for this year
            score = (
                analysis["completeness_percentage"] * 0.6 +  # Completeness weight
                analysis["confidence_score"] * 100 * 0.3 +   # Confidence weight
                analysis["data_freshness_score"] * 100 * 0.1  # Freshness weight
            )

            if score > best_year_score:
                best_year_score = score
                best_year = year

        result = {
            "years": years_analysis,
            "best_year": best_year,
            "best_score": best_year_score
        }

        # Cache the result
        self._year_cache[company_id] = result
        return result

    def _analyze_single_year(self, company_id: int, year: int) -> Dict[str, any]:
        """Analyze data quality for a specific company-year combination."""

        # Get all answers for this company-year
        answers = (
            self.db.query(Answer)
            .filter_by(company_id=company_id, year=year)
            .all()
        )

        total_expected = 151  # Total ESG indicators
        indicators_with_data = 0
        total_confidence = 0
        source_distribution = {"scraped": 0, "online_provisional": 0, "other_non_scraped": 0}
        verified_count = 0

        for answer in answers:
            if not (answer.answer_value and answer.answer_value.strip()):
                continue

            source = (getattr(answer, "source", "unknown") or "unknown").strip().lower()
            if not self._is_scraped_only_source(source):
                source_distribution["other_non_scraped"] += 1
                continue

            indicators_with_data += 1
            confidence = getattr(answer, 'confidence', 0.5) or 0.5
            total_confidence += confidence

            if source in source_distribution:
                source_distribution[source] += 1
            else:
                source_distribution["scraped"] += 1

            if getattr(answer, 'is_verified', False):
                verified_count += 1

        completeness_percentage = (indicators_with_data / total_expected) * 100
        avg_confidence = total_confidence / max(indicators_with_data, 1)
        verification_rate = (verified_count / max(indicators_with_data, 1)) * 100

        return {
            "year": year,
            "indicators_with_data": indicators_with_data,
            "total_indicators": total_expected,
            "completeness_percentage": round(completeness_percentage, 1),
            "confidence_score": round(avg_confidence, 2),
            "verification_rate": round(verification_rate, 1),
            "source_distribution": source_distribution,
            "data_freshness_score": self._calculate_data_freshness(year),
            "quality_grade": self._calculate_quality_grade(completeness_percentage, avg_confidence),
            "is_complete": indicators_with_data >= 140,  # Consider "complete" if missing <10 indicators
            "is_excellent": completeness_percentage >= 95.0 and avg_confidence >= 0.8
        }

    def _is_scraped_only_source(self, source: str) -> bool:
        """Strict source filter used for year-quality analysis."""
        src = (source or "").strip().lower()
        if not src:
            return False

        blocked_tokens = (
            "manual",
            "default",
            "template",
            "synthetic",
            "historical",
            "unavailable",
            "none",
        )
        return not any(token in src for token in blocked_tokens)

    def _select_perfect_year(self, year_analysis: Dict[str, any], requested_year: Optional[int]) -> int:
        """Select the perfect year to use for data retrieval."""

        years_data = year_analysis["years"]

        # If no specific year requested, use the best year
        if requested_year is None:
            return year_analysis["best_year"]

        # If requested year exists and has good data, use it
        if requested_year in years_data:
            requested_quality = years_data[requested_year]

            # Use requested year if it has decent quality (>80% complete)
            if requested_quality["completeness_percentage"] >= 80.0:
                return requested_year

        # Otherwise, use the best available year
        return year_analysis["best_year"]

    def _get_fallback_reason(self, requested_year: Optional[int], year_used: int, year_analysis: Dict) -> Optional[str]:
        """Get human-readable reason why we fell back to a different year."""

        if requested_year is None:
            return None

        if requested_year == year_used:
            return None

        if requested_year not in year_analysis["years"]:
            return f"Requested year {requested_year} has no data. Using {year_used} (best available)."

        requested_quality = year_analysis["years"][requested_year]["completeness_percentage"]
        used_quality = year_analysis["years"][year_used]["completeness_percentage"]

        return (
            f"Requested year {requested_year} has only {requested_quality}% data completeness. "
            f"Using {year_used} with {used_quality}% completeness for better results."
        )

    def _calculate_data_freshness(self, year: int) -> float:
        """Calculate how fresh/recent the data is (0-1 scale)."""
        import datetime
        current_year = datetime.datetime.now().year
        years_old = current_year - year

        # Fresh data gets higher score
        if years_old <= 1:
            return 1.0  # Very fresh
        elif years_old <= 2:
            return 0.8  # Fresh
        elif years_old <= 3:
            return 0.6  # Moderately fresh
        elif years_old <= 5:
            return 0.4  # Somewhat old
        else:
            return 0.2  # Old data

    def _calculate_quality_grade(self, completeness: float, confidence: float) -> str:
        """Calculate an overall quality grade (A-F)."""

        # Combined score from completeness and confidence
        score = (completeness * 0.7) + (confidence * 100 * 0.3)

        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def get_year_recommendations(self, company_id: int) -> List[Dict[str, any]]:
        """Get recommended years for a company with quality scores."""

        year_analysis = self._analyze_company_years(company_id)
        if not year_analysis:
            return []

        recommendations = []
        for year, data in sorted(year_analysis["years"].items(), key=lambda x: x[1]["completeness_percentage"], reverse=True):
            recommendations.append({
                "year": year,
                "completeness_percentage": data["completeness_percentage"],
                "quality_grade": data["quality_grade"],
                "is_recommended": data["is_excellent"],
                "indicators_count": f"{data['indicators_with_data']}/{data['total_indicators']}",
                "confidence_score": data["confidence_score"]
            })

        return recommendations