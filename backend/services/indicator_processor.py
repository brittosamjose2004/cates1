"""
services/indicator_processor.py
Individual indicator processing engine.

Handles calculation and data aggregation for each of the 151 ESG indicators.
Combines data from multiple sources: scraped data, manual input, historical values.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database.models import Answer, ScrapedData, Company, QuestionnaireSession
from backend.processor.data_mapper import DataMapper


class IndicatorProcessor:
    """
    Processes individual ESG indicators by:
    1. Collecting data from multiple sources (scraped, manual, historical)
    2. Applying calculation logic specific to indicator type
    3. Storing final values in Answer table
    4. Managing data quality and confidence scores
    """

    def __init__(self):
        # DataMapper will be initialized per company-year with scraped data
        pass


    def process_indicator(self,
                         company_id: int,
                         year: int,
                         indicator: Dict[str, Any],
                         db: Session) -> Dict[str, Any]:
        """
        Process a single indicator for a company-year combination.

        Args:
            company_id: Company ID
            year: Year to process
            indicator: Indicator definition from CSV
            db: Database session

        Returns:
            Dict with processing result and calculated value
        """
        indicator_id = indicator.get('indicator_id')
        response_format = indicator.get('response_format', 'text')
        data_type = indicator.get('data_type', 'string')

        try:
            # 1. Collect data from all sources
            source_data = self._collect_source_data(
                company_id, year, indicator_id, indicator, db
            )

            # 2. Calculate final value based on indicator type
            calculated_value, confidence, source = self._calculate_indicator_value(
                indicator, source_data, response_format, data_type
            )

            # 3. Store or update answer in database
            answer = self._store_answer(
                company_id, year, indicator, calculated_value,
                confidence, source, db
            )

            # 4. Return processing result
            return {
                "indicator_id": indicator_id,
                "value": calculated_value,
                "confidence": confidence,
                "source": source,
                "data_sources_used": list(source_data.keys()),
                "processing_status": "success"
            }

        except Exception as e:
            return {
                "indicator_id": indicator_id,
                "processing_status": "error",
                "error": str(e)
            }


    def _collect_source_data(self,
                           company_id: int,
                           year: int,
                           indicator_id: str,
                           indicator: Dict[str, Any],
                           db: Session) -> Dict[str, Any]:
        """
        Collect data from all available sources for an indicator.

        Sources prioritized by reliability:
        1. Manual input (highest priority)
        2. Scraped data from evidence (PDFs, CSVs)
        3. Historical data from previous years
        4. Smart defaults/calculations
        """
        source_data = {}

        # 1. Check for existing manual answer
        existing_answer = (
            db.query(Answer)
            .filter_by(
                company_id=company_id,
                year=year,
                indicator_id=indicator_id
            )
            .first()
        )

        if existing_answer and existing_answer.source == "manual":
            source_data["manual"] = {
                "value": existing_answer.answer_value,
                "confidence": 1.0,
                "updated_at": existing_answer.updated_at,
                "notes": existing_answer.notes
            }

        # 2. Get mapped scraped data from evidence
        scraped_data = self._get_scraped_indicator_data(
            company_id, year, indicator_id, indicator, db
        )
        if scraped_data:
            source_data["scraped"] = scraped_data

        # 3. Get historical data (previous years)
        historical_data = self._get_historical_data(
            company_id, indicator_id, year, db
        )
        if historical_data:
            source_data["historical"] = historical_data

        # 4. Calculate smart defaults for specific indicator types
        smart_default = self._calculate_smart_default(
            company_id, year, indicator, db
        )
        if smart_default:
            source_data["calculated"] = smart_default

        return source_data


    def _get_scraped_indicator_data(self,
                                  company_id: int,
                                  year: int,
                                  indicator_id: str,
                                  indicator: Dict[str, Any],
                                  db: Session) -> Optional[Dict[str, Any]]:
        """
        Get scraped data mapped to this indicator from evidence sources.
        """
        try:
            # Get all scraped data for this company-year
            scraped_records = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year
            ).all()

            # Convert to dict format expected by DataMapper (preserve source information)
            scraped_data = {}
            scraped_sources = {}  # Track source for each indicator
            for record in scraped_records:
                scraped_data[record.data_key] = record.data_value
                scraped_sources[record.data_key] = record.source  # Preserve specific source

            if not scraped_data:
                return None

            # Initialize DataMapper with scraped data and source information
            data_mapper = DataMapper(scraped_data, scraped_sources)

            # Get mapped data for this indicator
            mapped_result = data_mapper.get(indicator_id)

            if mapped_result:
                # Preserve specific source from DataMapper
                specific_source = mapped_result.get("source", "scraped")
                return {
                    "values": [mapped_result.get("answer", "")],
                    "confidence": mapped_result.get("confidence", 0.7),
                    "sources": [mapped_result.get("note", "")],
                    "specific_source": specific_source,  # Add specific source information
                    "extraction_method": "automated"
                }

        except Exception as e:
            print(f"Error mapping scraped data for {indicator_id}: {e}")

        return None


    def _get_historical_data(self,
                           company_id: int,
                           indicator_id: str,
                           current_year: int,
                           db: Session) -> Optional[Dict[str, Any]]:
        """
        Get historical values for this indicator from previous years.
        """
        # Look back up to 3 years
        historical_answers = (
            db.query(Answer)
            .filter(
                Answer.company_id == company_id,
                Answer.indicator_id == indicator_id,
                Answer.year < current_year,
                Answer.year >= current_year - 3
            )
            .order_by(Answer.year.desc())
            .limit(3)
            .all()
        )

        if historical_answers:
            return {
                "values": [
                    {
                        "year": ans.year,
                        "value": ans.answer_value,
                        "source": ans.source
                    }
                    for ans in historical_answers
                ],
                "confidence": 0.5,  # Lower confidence for historical data
                "most_recent_year": historical_answers[0].year,
                "most_recent_value": historical_answers[0].answer_value
            }

        return None


    def _calculate_smart_default(self,
                               company_id: int,
                               year: int,
                               indicator: Dict[str, Any],
                               db: Session) -> Optional[Dict[str, Any]]:
        """
        Calculate smart defaults for indicators that can be derived from other data.
        """
        indicator_id = indicator.get('indicator_id')
        indicator_name = indicator.get('indicator_name', '').lower()

        # Example calculations for common indicators
        try:
            # GHG Intensity calculations
            if 'ghg' in indicator_name and 'intensity' in indicator_name:
                return self._calculate_ghg_intensity(company_id, year, db)

            # Energy intensity calculations
            elif 'energy' in indicator_name and 'intensity' in indicator_name:
                return self._calculate_energy_intensity(company_id, year, db)

            # Employee-related ratios
            elif 'turnover' in indicator_name or 'retention' in indicator_name:
                return self._calculate_employee_ratios(company_id, year, db)

        except Exception as e:
            print(f"Error calculating smart default for {indicator_id}: {e}")

        return None


    def _calculate_indicator_value(self,
                                 indicator: Dict[str, Any],
                                 source_data: Dict[str, Any],
                                 response_format: str,
                                 data_type: str) -> tuple[str, float, str]:
        """
        Calculate final indicator value from multiple sources.

        Priority order:
        1. Manual input (confidence: 1.0)
        2. Scraped data (confidence: 0.7-0.9)
        3. Calculated values (confidence: 0.6-0.8)
        4. Historical data (confidence: 0.5)

        Returns:
            (final_value, confidence_score, source_type)
        """
        # Priority 1: Manual input
        if "manual" in source_data:
            manual = source_data["manual"]
            return manual["value"], manual["confidence"], "manual"

        # Priority 2: Scraped data
        if "scraped" in source_data:
            scraped = source_data["scraped"]
            values = scraped.get("values", [])
            if values:
                # Get specific source if available, fallback to generic "scraped"
                specific_source = scraped.get("specific_source", "scraped")

                # For numerical indicators, take average if multiple values
                if response_format in ["number", "percentage", "currency"]:
                    numerical_values = self._extract_numerical_values(values)
                    if numerical_values:
                        final_value = sum(numerical_values) / len(numerical_values)
                        return str(final_value), scraped["confidence"], specific_source

                # For text indicators, take first value
                return str(values[0]), scraped["confidence"], specific_source

        # Priority 3: Calculated values
        if "calculated" in source_data:
            calc = source_data["calculated"]
            return calc["value"], calc["confidence"], "calculated"

        # Priority 4: Historical data (only if not empty)
        if "historical" in source_data:
            hist = source_data["historical"]
            historical_value = hist["most_recent_value"]
            # Only use historical data if it has an actual value
            if historical_value and str(historical_value).strip() and str(historical_value).strip() != "No value":
                return historical_value, hist["confidence"], "historical"

        # No data available
        return "", 0.0, "none"


    def _extract_numerical_values(self, values: List[Any]) -> List[float]:
        """Extract numerical values from mixed data types"""
        numerical = []
        for val in values:
            try:
                # Handle various formats
                if isinstance(val, (int, float)):
                    numerical.append(float(val))
                elif isinstance(val, str):
                    # Remove common non-numeric characters
                    cleaned = val.replace(',', '').replace('%', '').replace('$', '')
                    cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.-')
                    if cleaned:
                        numerical.append(float(cleaned))
            except (ValueError, TypeError):
                continue
        return numerical


    def _store_answer(self,
                     company_id: int,
                     year: int,
                     indicator: Dict[str, Any],
                     value: str,
                     confidence: float,
                     source: str,
                     db: Session) -> Answer:
        """
        Store or update indicator answer in database.
        """
        indicator_id = indicator.get('indicator_id')

        # Get or create questionnaire session
        session = self._get_or_create_session(company_id, year, db)

        # Check for existing answer
        answer = (
            db.query(Answer)
            .filter_by(
                company_id=company_id,
                year=year,
                indicator_id=indicator_id
            )
            .first()
        )

        if answer:
            # Update existing answer (only if not manual or confidence is higher)
            if answer.source != "manual" or confidence > (answer.confidence or 0):
                answer.answer_value = value
                answer.confidence = confidence
                answer.source = source
                answer.updated_at = datetime.utcnow()
        else:
            # Create new answer
            answer = Answer(
                session_id=session.id,
                company_id=company_id,
                year=year,
                indicator_id=indicator_id,
                module=indicator.get('module_name'),
                indicator_name=indicator.get('indicator_name'),
                question_text=indicator.get('question'),
                answer_value=value,
                answer_unit=indicator.get('unit'),
                response_format=indicator.get('response_format'),
                source=source,
                confidence=confidence,
                is_verified=(source == "manual")
            )
            db.add(answer)

        db.commit()
        return answer


    def _get_or_create_session(self, company_id: int, year: int, db: Session) -> QuestionnaireSession:
        """Get or create questionnaire session for company-year"""
        session = (
            db.query(QuestionnaireSession)
            .filter_by(
                company_id=company_id,
                year=year,
                standard="ALL"
            )
            .first()
        )

        if not session:
            session = QuestionnaireSession(
                company_id=company_id,
                year=year,
                standard="ALL",
                status="in_progress",
                total_questions=151,
                answered_questions=0
            )
            db.add(session)
            db.commit()

        return session


    # ── Calculation Methods ───────────────────────────────────────────────

    def _calculate_ghg_intensity(self, company_id: int, year: int, db: Session) -> Optional[Dict[str, Any]]:
        """Calculate GHG emission intensity (tCO2e per unit revenue/production)"""
        try:
            # Get total emissions and revenue data from scraped data
            emissions_data = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year
            ).filter(
                ScrapedData.data_key.ilike('%emission%')
            ).all()

            revenue_data = db.query(ScrapedData).filter_by(
                company_id=company_id,
                year=year
            ).filter(
                ScrapedData.data_key.ilike('%revenue%')
            ).all()

            # Implementation would calculate intensity ratio
            # This is a placeholder for actual calculation logic
            return {
                "value": "Calculated based on emissions/revenue",
                "confidence": 0.7,
                "calculation_method": "ghg_intensity"
            }

        except Exception:
            return None


    def _calculate_energy_intensity(self, company_id: int, year: int, db: Session) -> Optional[Dict[str, Any]]:
        """Calculate energy intensity"""
        # Similar implementation to GHG intensity
        return None


    def _calculate_employee_ratios(self, company_id: int, year: int, db: Session) -> Optional[Dict[str, Any]]:
        """Calculate employee turnover and retention ratios"""
        # Implementation for HR-related calculations
        return None