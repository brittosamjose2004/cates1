"""
routers/companies.py — Company CRUD, risk scores, indicators, evidence.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.api.schemas import (
    CompanySummaryOut, CompanyDetailOut, AddCompanyRequest, CompanyCreatedOut,
    RiskScores, IndicatorOut, EvidenceItemOut, RiskPillarOut, DriverOut, DataQualityOut,
)
from backend.api.risk_engine import compute_risk_pillars, get_latest_year, get_pipeline_status
from backend.processor.csv_loader import ImpactreeCSVLoader
from backend.database.models import (
    Company, Answer, QuestionnaireSession, EvidenceSource, User, ScrapedData
)

router = APIRouter(prefix="/api/companies", tags=["companies"])

# ── Region heuristics ─────────────────────────────────────────────────────────

_REGION_MAP = {
    "india": "APAC", "in": "APAC", "apac": "APAC",
    "usa": "NA", "us": "NA", "united states": "NA", "na": "NA",
    "uk": "EU", "germany": "EU", "france": "EU", "eu": "EU",
    "brazil": "LATAM", "mexico": "LATAM", "latam": "LATAM",
    "uae": "EMEA", "saudi": "EMEA", "africa": "EMEA", "emea": "EMEA",
}

def _infer_region(company: Company) -> str:
    hq = (company.headquarters or "").lower()
    for key, region in _REGION_MAP.items():
        if key in hq:
            return region
    return "APAC"

def _time_ago(dt: Optional[datetime]) -> str:
    if not dt:
        return "Unknown"
    now = datetime.utcnow()
    diff = now - dt
    if diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} mins ago"
    if diff.days == 0:
        return f"{int(diff.total_seconds() // 3600)} hours ago"
    if diff.days == 1:
        return "1 day ago"
    return f"{diff.days} days ago"


def _is_scraped_only_source(source: Optional[str]) -> bool:
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


# ── GET /api/companies ───────────────────────────────────────────────────────

@router.get("", response_model=List[CompanySummaryOut])
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    result = []
    for c in companies:
        year = get_latest_year(db, c.id)
        pillars = compute_risk_pillars(db, c, year)
        pipeline_status = get_pipeline_status(db, c.id)

        result.append(CompanySummaryOut(
            id=str(c.id),
            name=c.name,
            ticker=c.ticker or "",
            lei=c.cin or "",
            region=_infer_region(c),
            sector=c.sector or "Unknown",
            status=pipeline_status,
            riskScores=RiskScores(
                s=pillars["sustainability"]["score"],
                p=pillars["pchi"]["score"],
                o=pillars["operational"]["score"],
                f=pillars["financial"]["score"],
            ),
            financialYear=f"FY{year}",
            lastUpdated=_time_ago(c.created_at),
        ))
    return result


# ── POST /api/companies ──────────────────────────────────────────────────────

@router.post("", response_model=CompanyCreatedOut, status_code=status.HTTP_201_CREATED)
def add_company(body: AddCompanyRequest, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name.ilike(f"%{body.name}%")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    company = Company(
        name=body.name,
        ticker=body.ticker or "",
        cin=body.lei or "",
        sector=body.sector or "Unknown",
        headquarters=body.region or "APAC",
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyCreatedOut(
        id=str(company.id),
        name=company.name,
        ticker=company.ticker or "",
        lei=company.cin or "",
        region=body.region or "APAC",
        sector=body.sector or "Unknown",
        status="QUEUED",
        riskScores=RiskScores(),
        financialYear=f"FY{body.financial_year or 2026}",
        lastUpdated="Just now",
    )


# ── GET /api/companies/{id} ──────────────────────────────────────────────────

@router.get("/{company_id}", response_model=CompanyDetailOut)
def get_company(company_id: str, year: Optional[int] = None, db: Session = Depends(get_db)):
    from backend.services.smart_year_resolver import SmartYearResolver

    company = db.query(Company).filter(Company.id == int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # ✨ NEW: Perfect year selection with quality analysis
    resolver = SmartYearResolver(db)
    perfect_data_info = resolver.get_perfect_year_data(company.id, year)

    if "error" in perfect_data_info:
        raise HTTPException(status_code=404, detail=perfect_data_info["error"])

    # Use the perfect year selected by resolver
    year_to_use = perfect_data_info["year_used"]

    pillars_raw = compute_risk_pillars(db, company, year_to_use)
    pipeline_status = get_pipeline_status(db, company.id)

    # ── Build pillars ──────────────────────────────────────────────────────
    pillars: dict = {}
    for key, p in pillars_raw.items():
        pillars[key] = RiskPillarOut(
            id=p["id"],
            name=p["name"],
            score=p["score"],
            trend=p["trend"],
            trendValue=p["trendValue"],
            drivers=[DriverOut(**d) for d in p["drivers"]],
        )

    # ── Build indicator list with perfect year-wise values ──────────────────
    answers = (
        db.query(Answer)
        .filter_by(company_id=company.id, year=year_to_use)
        .order_by(Answer.indicator_id)
        .all()
    )
    answer_map = {a.indicator_id: a for a in answers}

    indicator_defs = ImpactreeCSVLoader.get_all_indicators()
    indicators: List[IndicatorOut] = []

    for ind in indicator_defs:
        ind_id = ind.get("indicator_id", "")
        ind_name = ind.get("indicator_name") or ind_id
        ans = answer_map.get(ind_id)

        ans_source = (ans.source if ans else "") or ""
        source_is_scraped = _is_scraped_only_source(ans_source)

        if ans and ans.answer_value and source_is_scraped:
            val = ans.answer_value
            if len(val) > 220:
                val = val[:217].rstrip() + "..."

            # Use the source from Answer record (already contains dynamic sources from our fixes)
            specific_source = ans.source or "none"

            # Debug: Show what source we're using
            print(f"DEBUG: Using source '{specific_source}' for {ind_id}")

            # Create indicator with enhanced source information
            indicator = IndicatorOut(
                id=ind_id,
                name=ind_name,
                value=val,
                unit=ans.answer_unit or "",
                confidence=round((ans.confidence or 0.5) * 100, 0),
                source=specific_source,  # Use specific source instead of generic one
                isOverridden=ans.is_verified or False,
                overrideReason=ans.notes,
                lastUpdated=ans.updated_at.strftime("%Y-%m-%d") if ans.updated_at else str(year),
            )

            # Add detailed source tracking information using specific source
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from source_tracking_service import format_source_for_frontend
                source_details = format_source_for_frontend(specific_source, ind_id, company.id, year_to_use)  # Pass company_id and year
                indicator.source_details = source_details
            except ImportError:
                indicator.source_details = None

            indicators.append(indicator)
        else:
            indicator = IndicatorOut(
                id=ind_id,
                name=ind_name,
                value="",
                unit=(ans.answer_unit or "") if ans else "",
                confidence=0,
                source="unavailable",
                isOverridden=False,
                overrideReason=(
                    ans.notes
                    if ans and ans.answer_value and not source_is_scraped
                    else (ans.notes if ans else "No year-specific extracted data found")
                ),
                lastUpdated=ans.updated_at.strftime("%Y-%m-%d") if ans and ans.updated_at else str(year_to_use),
            )

            # Add source details for unavailable data too
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from source_tracking_service import format_source_for_frontend
                source_details = format_source_for_frontend("unavailable", ind_id, company.id, year_to_use)
                indicator.source_details = source_details
            except ImportError:
                indicator.source_details = None

            indicators.append(indicator)

    # ── Evidence ───────────────────────────────────────────────────────────
    evidence_rows = (
        db.query(EvidenceSource)
        .filter_by(company_id=company.id)
        .order_by(EvidenceSource.created_at.desc())
        .all()
    )
    evidence: List[EvidenceItemOut] = [
        EvidenceItemOut(
            id=str(e.id),
            type=e.type,
            name=e.name,
            date=e.date or "",
            status=e.status,
            tags=e.tags or [],
        )
        for e in evidence_rows
    ]

    # Determine version string with perfect year
    session = (
        db.query(QuestionnaireSession)
        .filter_by(company_id=company.id, year=year_to_use)
        .first()
    )
    version = f"v{year_to_use}.{session.id:04d}" if session else f"v{year_to_use}.0001"

    return CompanyDetailOut(
        id=str(company.id),
        name=company.name,
        ticker=company.ticker or "",
        lei=company.cin or "",
        sector=company.sector or "Unknown",
        financialYear=f"FY{year_to_use}",
        status=pipeline_status,
        lastUpdated=_time_ago(company.created_at),
        version=version,
        pillars=pillars,
        indicators=indicators,
        evidence=evidence,
        # ✨ NEW: Perfect data quality information
        dataQuality=DataQualityOut(
            requested_year=year,
            year_used=year_to_use,
            completeness_percentage=perfect_data_info["data_quality"]["completeness_percentage"],
            indicators_with_data=perfect_data_info["data_quality"]["indicators_with_data"],
            total_indicators=perfect_data_info["data_quality"]["total_indicators"],
            quality_grade=perfect_data_info["data_quality"]["quality_grade"],
            confidence_score=perfect_data_info["data_quality"]["confidence_score"],
            is_perfect_data=perfect_data_info["perfect_data"],
            fallback_reason=perfect_data_info["fallback_reason"],
            available_years=perfect_data_info["available_years"],
            data_freshness=perfect_data_info["data_freshness"]
        )
    )


# ── DELETE /api/companies/{id} ───────────────────────────────────────────────

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()


# ── GET /api/companies/{id}/years ─────────────────────────────────────────────


# ── GET /api/companies/{id}/real-data-analysis ───────────────────────────────

@router.get("/{company_id}/real-data-analysis")
def get_real_data_analysis(company_id: str, db: Session = Depends(get_db)):
    """
    Get comprehensive real data analysis for a company across all years.
    Shows data quality, sources, and recommendations for perfect real data retrieval.
    """
    from backend.services.real_data_validator import RealDataValidator

    try:
        company_id_int = int(company_id)
        validator = RealDataValidator(db)

        # Get comprehensive real data summary
        summary = validator.get_real_data_summary(company_id_int)

        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])

        # Get perfect real data info
        perfect_data_info = validator.get_perfect_real_data(company_id_int)

        return {
            "company_summary": summary,
            "perfect_data_recommendation": perfect_data_info,
            "real_data_sources": {
                "manual": "Manually entered data",
                "scraped": "Extracted from documents",
                "pdf_extracted": "Extracted from PDF documents",
                "annual_report": "From annual reports",
                "evidence_upload": "From uploaded evidence",
                "brsr_scraped": "From BRSR documents"
            },
            "synthetic_data_sources": {
                "online_provisional": "AI-generated provisional data",
                "online_scraped": "Web-scraped fallback data",
                "scribd_scraped": "Scribd fallback data",
                "calculated": "Calculated/estimated data"
            }
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ── GET /api/companies/{id}/validate-real-data/{year} ─────────────────────────

@router.get("/{company_id}/validate-real-data/{year}")
def validate_real_data_year(company_id: str, year: int, db: Session = Depends(get_db)):
    """
    Validate that a specific company-year combination contains only real data.
    Returns detailed breakdown of indicator sources.
    """
    from backend.services.real_data_validator import RealDataValidator

    try:
        company_id_int = int(company_id)
        validator = RealDataValidator(db)

        validation_result = validator.validate_real_data_only(company_id_int, year)

        return validation_result

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/{company_id}/year-recommendations")
def get_year_recommendations(company_id: str, db: Session = Depends(get_db)):
    """
    Get recommended years for a company with data quality analysis.
    Helps users choose the best year for perfect ESG data retrieval.
    """
    from backend.services.smart_year_resolver import SmartYearResolver

    company = db.query(Company).filter(Company.id == int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    resolver = SmartYearResolver(db)
    recommendations = resolver.get_year_recommendations(int(company_id))

    if not recommendations:
        return {
            "company_id": company_id,
            "company_name": company.name,
            "message": "No data available for this company",
            "recommendations": []
        }

    return {
        "company_id": company_id,
        "company_name": company.name,
        "total_years_available": len(recommendations),
        "best_year": recommendations[0]["year"] if recommendations else None,
        "recommendations": recommendations,
        "usage_guide": {
            "A+/A": "Perfect data - use without hesitation",
            "A-/B+": "Very good data - reliable for analysis",
            "B/B-": "Good data - suitable for most purposes",
            "C": "Moderate data - some gaps expected",
            "D/F": "Poor data - significant gaps, consider other years"
        }
    }


@router.get("/{company_id}/years")
def get_available_years(company_id: str, db: Session = Depends(get_db)):
    cid = int(company_id)

    session_years = {
        r.year for r in (
            db.query(QuestionnaireSession.year)
            .filter_by(company_id=cid)
            .distinct()
            .all()
        )
    }
    answer_years = {
        r.year for r in (
            db.query(Answer.year)
            .filter_by(company_id=cid)
            .distinct()
            .all()
        )
    }
    scraped_years = {
        r.year for r in (
            db.query(ScrapedData.year)
            .filter_by(company_id=cid)
            .distinct()
            .all()
        )
    }

    years = sorted(session_years | answer_years | scraped_years, reverse=True)
    return {"years": [f"FY{y}" for y in years]}
