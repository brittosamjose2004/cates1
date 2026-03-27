"""
services/scoring_engine.py
ESG scoring and rating calculation engine.

Calculates final ESG scores based on processed indicators across all modules.
Supports multiple scoring methodologies and standards compliance.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import math

from backend.database.models import Answer, Company
from backend.processor.csv_loader import ImpactreeCSVLoader


class ScoringEngine:
    """
    Calculates ESG scores and ratings using multiple methodologies:

    1. Weighted scoring based on indicator priority
    2. Module-level scoring (21 modules)
    3. Standard-specific scoring (BRSR, CDP, EcoVadis, GRI)
    4. Benchmark-based rating (A, B, C, D, E)
    5. Trend analysis vs. previous years
    """

    def __init__(self):
        # Scoring weights by standard
        self.standard_weights = {
            'BRSR': 0.4,    # Indian regulatory standard (highest weight)
            'CDP': 0.25,    # Climate focus
            'EcoVadis': 0.2,  # Business sustainability
            'GRI': 0.15     # Global reporting standard
        }

        # Module weights by importance (can be customized)
        self.module_weights = {
            "GHG Emissions & Climate Change": 0.20,
            "Governance & Ethics": 0.15,
            "Occupational Health & Safety (OHS)": 0.12,
            "Supply Chain & Procurement": 0.10,
            "Labor & Human Rights": 0.08,
            "Energy": 0.06,
            "Water & Effluents": 0.05,
            "Waste & Materials": 0.05,
            "Risk & Opportunity Management": 0.04,
            "Sustainability Management & Reporting": 0.04,
            "Economic Performance": 0.04,
            "Legal & Environmental Compliance": 0.03,
            "Community & Social Impact": 0.02,
            "General & Organizational Profile": 0.02
        }

        # Rating thresholds (0-100 scale)
        self.rating_thresholds = {
            'A': 85,  # Excellent
            'B': 70,  # Good
            'C': 55,  # Average
            'D': 40,  # Below Average
            'E': 0    # Poor
        }


    def calculate_company_scores(self,
                               company_id: int,
                               year: int,
                               standards: List[str],
                               db: Session) -> Dict[str, Any]:
        """
        Calculate comprehensive ESG scores for a company-year.

        Returns:
            Dict containing overall score, module scores, standard scores, and rating
        """
        try:
            # 1. Get all answered indicators for the company-year
            answers = self._get_company_answers(company_id, year, db)

            # 2. Calculate module-level scores
            module_scores = self._calculate_module_scores(answers, standards)

            # 3. Calculate overall ESG score
            overall_score = self._calculate_overall_score(module_scores)

            # 4. Calculate standard-specific scores
            standard_scores = self._calculate_standard_scores(answers, standards)

            # 5. Determine letter rating
            letter_rating = self._calculate_letter_rating(overall_score)

            # 6. Calculate trend vs. previous year
            trend_analysis = self._calculate_trend(company_id, year, overall_score, db)

            # 7. Generate score breakdown
            score_breakdown = self._generate_score_breakdown(
                answers, module_scores, standard_scores
            )

            return {
                "company_id": company_id,
                "year": year,
                "overall_score": round(overall_score, 1),
                "letter_rating": letter_rating,
                "module_scores": module_scores,
                "standard_scores": standard_scores,
                "trend_analysis": trend_analysis,
                "score_breakdown": score_breakdown,
                "calculation_date": datetime.utcnow().isoformat(),
                "total_indicators_scored": len(answers),
                "scoring_confidence": self._calculate_scoring_confidence(answers)
            }

        except Exception as e:
            return {
                "error": f"Scoring calculation failed: {str(e)}",
                "company_id": company_id,
                "year": year
            }


    def _get_company_answers(self, company_id: int, year: int, db: Session) -> List[Answer]:
        """Get all answers for company-year with valid values"""
        return db.query(Answer).filter(
            Answer.company_id == company_id,
            Answer.year == year,
            Answer.answer_value.isnot(None),
            Answer.answer_value != ""
        ).all()


    def _calculate_module_scores(self, answers: List[Answer],
                               standards: List[str]) -> Dict[str, float]:
        """Calculate scores for each ESG module"""

        # Group answers by module
        module_answers = {}
        for answer in answers:
            module = answer.module or "Unknown"
            if module not in module_answers:
                module_answers[module] = []
            module_answers[module].append(answer)

        module_scores = {}

        for module, module_answer_list in module_answers.items():
            module_score = self._calculate_single_module_score(
                module, module_answer_list, standards
            )
            module_scores[module] = round(module_score, 1)

        return module_scores


    def _calculate_single_module_score(self,
                                     module_name: str,
                                     answers: List[Answer],
                                     standards: List[str]) -> float:
        """Calculate score for a single module"""

        if not answers:
            return 0.0

        # Get indicator priorities for weighting
        indicator_scores = []

        for answer in answers:
            # Base score calculation
            indicator_score = self._calculate_indicator_score(answer)

            # Apply confidence weighting
            confidence = answer.confidence or 0.5
            weighted_score = indicator_score * confidence

            # Apply priority weighting (if available from CSV)
            priority_weight = self._get_indicator_priority_weight(answer.indicator_id)
            final_score = weighted_score * priority_weight

            indicator_scores.append(final_score)

        # Calculate module average
        if indicator_scores:
            return sum(indicator_scores) / len(indicator_scores)
        else:
            return 0.0


    def _calculate_indicator_score(self, answer: Answer) -> float:
        """
        Calculate score for individual indicator based on response format.

        Returns score on 0-100 scale.
        """
        response_format = answer.response_format or "text"
        value = answer.answer_value or ""

        if not value.strip():
            return 0.0

        try:
            if response_format == "boolean":
                return 100.0 if value.lower() in ["yes", "true", "1"] else 0.0

            elif response_format == "percentage":
                # Extract numerical percentage
                percent_value = self._extract_number(value)
                return min(percent_value, 100.0) if percent_value is not None else 50.0

            elif response_format == "number":
                # Numerical indicators need context-specific scoring
                return self._score_numerical_indicator(answer)

            elif response_format in ["text", "description", "url"]:
                # Quality-based scoring for text responses
                return self._score_text_quality(value)

            elif response_format == "currency":
                # Currency indicators (investment amounts, etc.)
                return self._score_currency_indicator(answer)

            elif response_format == "date":
                # Date-based scoring (recency, compliance dates)
                return self._score_date_indicator(value)

            else:
                # Default scoring for unknown formats
                return 50.0 if value.strip() else 0.0

        except Exception:
            return 25.0  # Default partial score for errors


    def _calculate_overall_score(self, module_scores: Dict[str, float]) -> float:
        """Calculate weighted overall ESG score"""

        if not module_scores:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for module_name, score in module_scores.items():
            weight = self.module_weights.get(module_name, 0.01)  # Default minimal weight
            weighted_sum += score * weight
            total_weight += weight

        # Normalize if total weight != 1.0
        if total_weight > 0:
            return (weighted_sum / total_weight)
        else:
            return sum(module_scores.values()) / len(module_scores)


    def _calculate_standard_scores(self, answers: List[Answer],
                                 standards: List[str]) -> Dict[str, float]:
        """Calculate scores by ESG standard (BRSR, CDP, EcoVadis, GRI)"""

        # Load standard mappings from questionnaire CSV
        questionnaire_df = ImpactreeCSVLoader.questionnaire()

        standard_scores = {}

        for standard in standards:
            if standard == "ALL":
                continue

            # Get indicators mapped to this standard
            standard_column = standard.lower()
            if standard_column in questionnaire_df.columns:
                standard_indicators = questionnaire_df[
                    questionnaire_df[standard_column].notna() &
                    (questionnaire_df[standard_column] != 0)
                ]['indicator_id'].tolist()

                # Get answers for this standard's indicators
                standard_answers = [
                    ans for ans in answers
                    if ans.indicator_id in standard_indicators
                ]

                # Calculate standard score
                if standard_answers:
                    indicator_scores = [
                        self._calculate_indicator_score(ans)
                        for ans in standard_answers
                    ]
                    standard_scores[standard] = round(
                        sum(indicator_scores) / len(indicator_scores), 1
                    )
                else:
                    standard_scores[standard] = 0.0

        return standard_scores


    def _calculate_letter_rating(self, overall_score: float) -> str:
        """Convert numerical score to letter rating"""

        for rating, threshold in self.rating_thresholds.items():
            if overall_score >= threshold:
                return rating

        return 'E'  # Fallback to lowest rating


    def _calculate_trend(self, company_id: int, year: int,
                       current_score: float, db: Session) -> Dict[str, Any]:
        """Calculate trend analysis vs. previous years"""

        # This would require storing historical scores
        # For now, return placeholder structure

        return {
            "previous_year_score": None,
            "year_over_year_change": None,
            "trend_direction": "stable",
            "improvement_areas": [],
            "declining_areas": []
        }


    def _generate_score_breakdown(self,
                                answers: List[Answer],
                                module_scores: Dict[str, float],
                                standard_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate detailed score breakdown for transparency"""

        # Data completeness analysis
        total_possible_indicators = 151  # From data summary
        answered_indicators = len(answers)
        completeness_rate = (answered_indicators / total_possible_indicators) * 100

        # Confidence distribution
        confidence_levels = [ans.confidence or 0.5 for ans in answers]
        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0

        # Top performing modules
        sorted_modules = sorted(
            module_scores.items(), key=lambda x: x[1], reverse=True
        )
        top_modules = sorted_modules[:5]
        improvement_modules = sorted_modules[-3:]

        return {
            "data_completeness_rate": round(completeness_rate, 1),
            "answered_indicators": answered_indicators,
            "total_possible_indicators": total_possible_indicators,
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_indicators": len([
                c for c in confidence_levels if c >= 0.8
            ]),
            "top_performing_modules": top_modules,
            "improvement_opportunity_modules": improvement_modules,
            "manual_vs_automated": self._analyze_data_sources(answers)
        }


    def _calculate_scoring_confidence(self, answers: List[Answer]) -> float:
        """Calculate overall confidence in the scoring"""

        if not answers:
            return 0.0

        # Factors affecting confidence:
        # 1. Data completeness
        # 2. Answer confidence levels
        # 3. Source reliability (manual > scraped > calculated > historical)

        completeness_factor = min(len(answers) / 151, 1.0)  # Max 100% for all 151 indicators

        confidence_scores = [ans.confidence or 0.5 for ans in answers]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)

        # Source reliability weighting
        source_weights = {"manual": 1.0, "scraped": 0.8, "calculated": 0.6, "historical": 0.4}
        source_reliability = sum(
            source_weights.get(ans.source, 0.3) for ans in answers
        ) / len(answers)

        # Combined confidence score
        overall_confidence = (completeness_factor * 0.4 + avg_confidence * 0.4 + source_reliability * 0.2)

        return round(overall_confidence, 2)


    # ── Helper Methods ─────────────────────────────────────────────────────

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numerical value from text"""
        try:
            # Remove common non-numeric characters
            cleaned = text.replace(',', '').replace('%', '').replace('$', '')
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.-')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None


    def _get_indicator_priority_weight(self, indicator_id: str) -> float:
        """Get priority weight for indicator from CSV data"""
        try:
            questionnaire_df = ImpactreeCSVLoader.questionnaire()
            priority_row = questionnaire_df[
                questionnaire_df['indicator_id'] == indicator_id
            ]

            if not priority_row.empty:
                priority = priority_row['priority'].iloc[0]
                if priority == 'High':
                    return 1.5
                elif priority == 'Medium':
                    return 1.0
                else:
                    return 0.8
        except Exception:
            pass

        return 1.0  # Default weight


    def _score_numerical_indicator(self, answer: Answer) -> float:
        """Score numerical indicators based on context"""
        value = self._extract_number(answer.answer_value or "")
        if value is None:
            return 0.0

        indicator_name = (answer.indicator_name or "").lower()

        # Efficiency indicators (higher is better)
        if any(term in indicator_name for term in ["efficiency", "renewable", "recycling"]):
            return min(value, 100.0)

        # Negative indicators (lower is better)
        elif any(term in indicator_name for term in ["emission", "waste", "injury", "turnover"]):
            # Use inverse scoring - implementation would need benchmarks
            return max(100.0 - (value / 10), 0.0)

        # Amount indicators (presence is good)
        else:
            return 75.0 if value > 0 else 0.0


    def _score_text_quality(self, text: str) -> float:
        """Score text responses based on quality indicators"""
        if not text.strip():
            return 0.0

        length = len(text.strip())

        # Quality indicators
        score = 30.0  # Base score for any response

        if length > 50:
            score += 20.0  # Detailed response
        if length > 200:
            score += 20.0  # Comprehensive response
        if any(word in text.lower() for word in ["policy", "procedure", "target", "metric"]):
            score += 15.0  # Contains policy/process terms
        if any(word in text.lower() for word in ["annual", "monthly", "regularly", "systematic"]):
            score += 15.0  # Contains process frequency terms

        return min(score, 100.0)


    def _score_currency_indicator(self, answer: Answer) -> float:
        """Score currency indicators (investment amounts, etc.)"""
        value = self._extract_number(answer.answer_value or "")
        if value is None or value <= 0:
            return 0.0

        # Any positive investment/expenditure gets good score
        return 80.0


    def _score_date_indicator(self, date_str: str) -> float:
        """Score date indicators based on recency"""
        try:
            # Simple date scoring - recent dates get higher scores
            if any(term in date_str for term in ["2024", "2025", "2026"]):
                return 90.0
            elif any(term in date_str for term in ["2022", "2023"]):
                return 70.0
            else:
                return 50.0
        except Exception:
            return 25.0


    def _analyze_data_sources(self, answers: List[Answer]) -> Dict[str, int]:
        """Analyze distribution of data sources"""
        source_counts = {}
        for answer in answers:
            source = answer.source or "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts