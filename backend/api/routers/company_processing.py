"""
api/routers/company_processing.py
REST API endpoints for company year-wise ESG data processing.

Provides endpoints to:
- Trigger complete company-year processing
- Monitor processing status and progress
- Retrieve scores and reports
- Manage processing pipelines
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.database.models import Company, PipelineJob, Answer
from backend.services.company_year_processor import CompanyYearProcessor, process_company_year
from backend.services.scoring_engine import ScoringEngine


router = APIRouter(prefix="/api/companies/{company_id}/processing", tags=["company-processing"])


# ── Data Models ────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


class ProcessingRequest(BaseModel):
    year: int = Field(..., ge=2020, le=2030, description="Year to process (2020-2030)")
    standards: Optional[List[str]] = Field(
        default=["BRSR", "CDP", "EcoVadis", "GRI"],
        description="ESG standards to include"
    )
    force_refresh: bool = Field(default=False, description="Force re-processing")
    include_real_time: bool = Field(default=True, description="Include real-time data")
    trigger_scoring: bool = Field(default=True, description="Calculate scores and ratings")


class ProcessingStatus(BaseModel):
    job_id: int
    company_id: int
    year: int
    status: str  # QUEUED | PROCESSING | COMPLETED | ERROR
    progress_percentage: Optional[float] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None
    processing_stats: Optional[dict] = None


class ProcessingResult(BaseModel):
    company_id: int
    year: int
    overall_score: Optional[float] = None
    letter_rating: Optional[str] = None
    total_indicators: int
    processed_indicators: int
    failed_indicators: int
    modules_processed: List[str]
    processing_time_seconds: float
    final_score: Optional[float] = None
    module_scores: Optional[dict] = None
    errors: Optional[List[str]] = None


class ScoreBreakdown(BaseModel):
    overall_score: float
    letter_rating: str
    module_scores: dict
    standard_scores: dict
    trend_analysis: dict
    data_completeness_rate: float
    scoring_confidence: float


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/trigger", response_model=ProcessingStatus)
async def trigger_processing(
    company_id: str,
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger complete ESG data processing for a company-year.

    This starts a background job that:
    1. Processes all 21 ESG modules
    2. Calculates 151 indicators
    3. Generates scores and ratings
    4. Creates comprehensive reports
    """
    # Validate company exists
    company = db.query(Company).filter_by(id=int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check if processing already running
    existing_job = (
        db.query(PipelineJob)
        .filter_by(
            company_id=int(company_id),
            year=request.year,
            status="PROCESSING"
        )
        .first()
    )

    if existing_job and not request.force_refresh:
        raise HTTPException(
            status_code=409,
            detail=f"Processing already running for {company.name} year {request.year}"
        )

    # Create pipeline job
    pipeline_job = PipelineJob(
        company_id=int(company_id),
        company_name=company.name,
        year=request.year,
        status="QUEUED",
        data_sources=request.standards,
        triggered_by="API"
    )
    db.add(pipeline_job)
    db.commit()
    db.refresh(pipeline_job)

    # Start background processing
    background_tasks.add_task(
        _process_company_year_background,
        int(company_id),
        request.year,
        pipeline_job.id,
        request.dict()
    )

    return ProcessingStatus(
        job_id=pipeline_job.id,
        company_id=int(company_id),
        year=request.year,
        status="QUEUED",
        started_at=pipeline_job.started_at.isoformat() if pipeline_job.started_at else None
    )


@router.get("/status/{year}", response_model=ProcessingStatus)
def get_processing_status(
    company_id: str,
    year: int,
    db: Session = Depends(get_db)
):
    """Get current processing status for a company-year."""

    # Find most recent pipeline job for this company-year
    pipeline_job = (
        db.query(PipelineJob)
        .filter_by(company_id=int(company_id), year=year)
        .order_by(PipelineJob.started_at.desc())
        .first()
    )

    if not pipeline_job:
        raise HTTPException(
            status_code=404,
            detail=f"No processing job found for company {company_id} year {year}"
        )

    # Calculate progress if processing
    progress = None
    if pipeline_job.status == "PROCESSING":
        progress = _calculate_processing_progress(int(company_id), year, db)

    return ProcessingStatus(
        job_id=pipeline_job.id,
        company_id=int(company_id),
        year=year,
        status=pipeline_job.status,
        progress_percentage=progress,
        started_at=pipeline_job.started_at.isoformat() if pipeline_job.started_at else None,
        finished_at=pipeline_job.finished_at.isoformat() if pipeline_job.finished_at else None,
        error_message=pipeline_job.error_msg
    )


@router.get("/results/{year}", response_model=ProcessingResult)
def get_processing_results(
    company_id: str,
    year: int,
    db: Session = Depends(get_db)
):
    """Get detailed processing results for a completed company-year processing."""

    # Check if processing is completed
    pipeline_job = (
        db.query(PipelineJob)
        .filter_by(
            company_id=int(company_id),
            year=year,
            status="COMPLETED"
        )
        .order_by(PipelineJob.started_at.desc())
        .first()
    )

    if not pipeline_job:
        raise HTTPException(
            status_code=404,
            detail=f"No completed processing found for company {company_id} year {year}"
        )

    # Get processing statistics
    answers = db.query(Answer).filter_by(
        company_id=int(company_id),
        year=year
    ).all()

    # Calculate basic stats
    total_indicators = 151
    processed_indicators = len(answers)
    failed_indicators = total_indicators - processed_indicators

    # Get modules with data
    modules_processed = list(set(
        ans.module for ans in answers if ans.module
    ))

    # Calculate processing time
    processing_time = 0
    if pipeline_job.started_at and pipeline_job.finished_at:
        processing_time = (
            pipeline_job.finished_at - pipeline_job.started_at
        ).total_seconds()

    return ProcessingResult(
        company_id=int(company_id),
        year=year,
        total_indicators=total_indicators,
        processed_indicators=processed_indicators,
        failed_indicators=failed_indicators,
        modules_processed=modules_processed,
        processing_time_seconds=processing_time
    )


@router.get("/scores/{year}", response_model=ScoreBreakdown)
def get_company_scores(
    company_id: str,
    year: int,
    standards: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """Get ESG scores and ratings for a company-year."""

    # Validate company and year
    company = db.query(Company).filter_by(id=int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check if we have processed data for this year
    answers_exist = db.query(Answer).filter_by(
        company_id=int(company_id),
        year=year
    ).first()

    if not answers_exist:
        raise HTTPException(
            status_code=404,
            detail=f"No processed data found for {company.name} year {year}"
        )

    # Calculate scores
    scoring_engine = ScoringEngine()
    scores = scoring_engine.calculate_company_scores(
        int(company_id),
        year,
        standards or ["BRSR", "CDP", "EcoVadis", "GRI"],
        db
    )

    if "error" in scores:
        raise HTTPException(status_code=500, detail=scores["error"])

    return ScoreBreakdown(
        overall_score=scores.get("overall_score", 0),
        letter_rating=scores.get("letter_rating", "E"),
        module_scores=scores.get("module_scores", {}),
        standard_scores=scores.get("standard_scores", {}),
        trend_analysis=scores.get("trend_analysis", {}),
        data_completeness_rate=scores.get("score_breakdown", {}).get("data_completeness_rate", 0),
        scoring_confidence=scores.get("scoring_confidence", 0)
    )


@router.get("/history", response_model=List[ProcessingStatus])
def get_processing_history(
    company_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get processing history for a company."""

    pipeline_jobs = (
        db.query(PipelineJob)
        .filter_by(company_id=int(company_id))
        .order_by(PipelineJob.started_at.desc())
        .limit(limit)
        .all()
    )

    return [
        ProcessingStatus(
            job_id=job.id,
            company_id=int(company_id),
            year=job.year or 0,
            status=job.status,
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
            error_message=job.error_msg
        )
        for job in pipeline_jobs
    ]


@router.delete("/cancel/{year}")
def cancel_processing(
    company_id: str,
    year: int,
    db: Session = Depends(get_db)
):
    """Cancel ongoing processing for a company-year."""

    pipeline_job = (
        db.query(PipelineJob)
        .filter_by(
            company_id=int(company_id),
            year=year,
            status="PROCESSING"
        )
        .first()
    )

    if not pipeline_job:
        raise HTTPException(
            status_code=404,
            detail="No active processing found to cancel"
        )

    pipeline_job.status = "CANCELLED"
    pipeline_job.finished_at = pipeline_job.started_at  # Set finish time
    db.commit()

    return {"message": f"Processing cancelled for company {company_id} year {year}"}


# ── Background Processing ─────────────────────────────────────────────────

def _process_company_year_background(
    company_id: int,
    year: int,
    job_id: int,
    request_params: dict
):
    """
    Background task for company-year processing.
    """
    try:
        # Create processor
        processor = CompanyYearProcessor(
            str(company_id),
            year,
            request_params.get("standards", ["BRSR", "CDP", "EcoVadis", "GRI"])
        )

        # Update job status to processing
        db = processor.db
        if db is None:
            processor._initialize_session()
            db = processor.db

        pipeline_job = db.query(PipelineJob).filter_by(id=job_id).first()
        if pipeline_job:
            pipeline_job.status = "PROCESSING"
            db.commit()

        # Run processing
        result = processor.process_company_year(
            force_refresh=request_params.get("force_refresh", False),
            include_real_time=request_params.get("include_real_time", True),
            trigger_scoring=request_params.get("trigger_scoring", True)
        )

        # Update job with success
        if pipeline_job:
            pipeline_job.status = "COMPLETED"
            pipeline_job.finished_at = result.start_time if hasattr(result, 'start_time') else None
            db.commit()

    except Exception as e:
        # Update job with error
        try:
            from backend.database.db import get_session
            db = get_session()
            pipeline_job = db.query(PipelineJob).filter_by(id=job_id).first()
            if pipeline_job:
                pipeline_job.status = "ERROR"
                pipeline_job.error_msg = str(e)
                db.commit()
            db.close()
        except Exception:
            print(f"Failed to update job {job_id} with error: {e}")


def _calculate_processing_progress(company_id: int, year: int, db: Session) -> float:
    """Calculate processing progress percentage."""

    try:
        # Count processed indicators
        answered_indicators = db.query(Answer).filter_by(
            company_id=company_id,
            year=year
        ).count()

        # Total possible indicators
        total_indicators = 151

        progress = (answered_indicators / total_indicators) * 100
        return round(progress, 1)

    except Exception:
        return 0.0