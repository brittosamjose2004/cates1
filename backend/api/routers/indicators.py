"""
routers/indicators.py — Get all 151 ESG indicator values for companies
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.database.models import Company, Answer
from backend.processor.csv_loader import ImpactreeCSVLoader

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

@router.get("/list")
def get_all_indicators():
    """Get the complete list of all 151 ESG indicators with their metadata."""
    try:
        indicators = ImpactreeCSVLoader.get_all_indicators()

        return {
            "total_indicators": len(indicators),
            "indicators": [
                {
                    "indicator_id": ind.get("indicator_id"),
                    "module_name": ind.get("module_name"),
                    "indicator_name": ind.get("indicator_name"),
                    "question": ind.get("question"),
                    "response_format": ind.get("response_format"),
                    "data_type": ind.get("data_type"),
                    "standards_covered": ind.get("Standards\nCovered", 0),
                    "brsr": "✓" if ind.get("brsr") == "✓" else "",
                    "cdp": "✓" if ind.get("cdp") == "✓" else "",
                    "ecovadis": "✓" if ind.get("ecovadis") == "✓" else "",
                    "gri": "✓" if ind.get("gri") == "✓" else "",
                    "priority": ind.get("priority"),
                    "guidance": ind.get("guidance")
                }
                for ind in indicators
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading indicators: {str(e)}")

@router.get("/values/{company_id}/{year}")
def get_indicator_values(
    company_id: int,
    year: int,
    db: Session = Depends(get_db),
    include_empty: bool = Query(False, description="Include indicators with no values"),
    standard: str = Query("ALL", description="Filter by standard: BRSR, CDP, EcoVadis, GRI, or ALL")
):
    """
    Get all 151 ESG indicator values for a specific company and year.

    Returns actual answer values from the database along with indicator metadata.
    """
    try:
        # Verify company exists
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get all indicators (filtered by standard if specified)
        if standard.upper() == "ALL":
            indicators = ImpactreeCSVLoader.get_all_indicators()
        else:
            indicators = ImpactreeCSVLoader.get_indicators_by_standard(standard.upper())

        # Get all answers for this company-year
        answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        # Create a mapping of indicator_id to answer
        answer_map = {answer.indicator_id: answer for answer in answers}

        # Prepare result with indicator metadata + values
        result = []
        indicators_with_values = 0
        indicators_without_values = 0

        for indicator in indicators:
            indicator_id = indicator.get("indicator_id")
            answer = answer_map.get(indicator_id)

            has_value = answer and answer.answer_value is not None and answer.answer_value != ""

            if has_value:
                indicators_with_values += 1
            else:
                indicators_without_values += 1

            # Include this indicator if it has a value OR if include_empty is True
            if has_value or include_empty:
                indicator_data = {
                    "indicator_id": indicator_id,
                    "module_name": indicator.get("module_name"),
                    "indicator_name": indicator.get("indicator_name"),
                    "question": indicator.get("question"),
                    "response_format": indicator.get("response_format"),
                    "data_type": indicator.get("data_type"),
                    "standards_covered": indicator.get("Standards\nCovered", 0),

                    # Answer data
                    "has_value": has_value,
                    "answer_value": answer.answer_value if answer else None,
                    "source": answer.source if answer else None,
                    "confidence": answer.confidence if answer else None,
                    "is_verified": answer.is_verified if answer else False,
                    "notes": answer.notes if answer else None,
                    "updated_at": answer.updated_at.isoformat() if answer and answer.updated_at else None
                }
                result.append(indicator_data)

        return {
            "company_id": company_id,
            "company_name": company.name,
            "year": year,
            "standard_filter": standard,
            "total_indicators_available": len(indicators),
            "indicators_with_values": indicators_with_values,
            "indicators_without_values": indicators_without_values,
            "completion_rate": round((indicators_with_values / len(indicators)) * 100, 1) if indicators else 0,
            "indicators": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving indicator values: {str(e)}")

@router.get("/summary/{company_id}/{year}")
def get_indicator_summary(
    company_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get a summary of ESG indicator completion rates by module for a company-year.
    """
    try:
        # Verify company exists
        company = db.query(Company).filter_by(id=company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get all indicators
        indicators = ImpactreeCSVLoader.get_all_indicators()

        # Get all answers for this company-year
        answers = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).all()

        answer_map = {answer.indicator_id: answer for answer in answers}

        # Group by module
        module_stats = {}

        for indicator in indicators:
            module_name = indicator.get("module_name")
            indicator_id = indicator.get("indicator_id")

            if module_name not in module_stats:
                module_stats[module_name] = {
                    "total_indicators": 0,
                    "indicators_with_values": 0,
                    "completion_rate": 0
                }

            module_stats[module_name]["total_indicators"] += 1

            answer = answer_map.get(indicator_id)
            if answer and answer.answer_value is not None and answer.answer_value != "":
                module_stats[module_name]["indicators_with_values"] += 1

        # Calculate completion rates
        for module_name, stats in module_stats.items():
            if stats["total_indicators"] > 0:
                stats["completion_rate"] = round(
                    (stats["indicators_with_values"] / stats["total_indicators"]) * 100, 1
                )

        # Sort by completion rate (highest first)
        sorted_modules = sorted(
            module_stats.items(),
            key=lambda x: x[1]["completion_rate"],
            reverse=True
        )

        total_with_values = sum(stats["indicators_with_values"] for stats in module_stats.values())

        return {
            "company_id": company_id,
            "company_name": company.name,
            "year": year,
            "overall_summary": {
                "total_indicators": len(indicators),
                "indicators_with_values": total_with_values,
                "indicators_without_values": len(indicators) - total_with_values,
                "completion_rate": round((total_with_values / len(indicators)) * 100, 1) if indicators else 0
            },
            "module_breakdown": [
                {
                    "module_name": module_name,
                    **stats
                }
                for module_name, stats in sorted_modules
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")