"""
FastAPI REST API server for programmatic access to the prompt optimizer.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agents import OrchestratorAgent
from database import db, User, BatchJob
from batch_optimization import BatchOptimizer
from ab_testing import ABTesting
from export_utils import export_results
from input_validation import sanitize_and_validate_prompt, validate_prompt_type
from monitoring import get_health_checker, get_metrics

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NextEleven AI Prompt Optimizer API",
    description="REST API for programmatic access to prompt optimization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# Pydantic models
class OptimizeRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to optimize")
    prompt_type: str = Field(default="creative", description="Type of prompt")


class OptimizeResponse(BaseModel):
    success: bool
    original_prompt: str
    optimized_prompt: Optional[str] = None
    quality_score: Optional[int] = None
    deconstruction: Optional[str] = None
    diagnosis: Optional[str] = None
    evaluation: Optional[str] = None
    sample_output: Optional[str] = None
    error: Optional[str] = None


class BatchOptimizeRequest(BaseModel):
    prompts: List[Dict[str, str]] = Field(..., description="List of prompts with 'prompt' and 'type' keys")
    name: Optional[str] = None


class BatchOptimizeResponse(BaseModel):
    job_id: int
    status: str
    total_prompts: int


class ABTestRequest(BaseModel):
    name: str
    original_prompt: str
    variant_a: Optional[str] = None
    variant_b: Optional[str] = None


class ExportRequest(BaseModel):
    results: Dict[str, Any]
    format: str = Field(default="json", description="Export format: json, markdown, or pdf")


# Authentication (Beta mode: Optional)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user from API key (optional for beta)."""
    if not credentials:
        return None  # Beta mode: Allow anonymous access
    api_key = credentials.credentials
    user = db.get_user_by_api_key(api_key)
    return user  # Return None if invalid (beta mode allows this)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user (beta mode: always allows, returns None if no auth)."""
    return await get_current_user_optional(credentials)


# API Endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "NextEleven AI Prompt Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_checker = get_health_checker()
    return health_checker.check_all()


@app.get("/metrics")
async def get_metrics_endpoint():
    """Get application metrics."""
    metrics = get_metrics()
    return metrics.get_all_metrics()


@app.post("/api/v1/optimize", response_model=OptimizeResponse)
async def optimize_prompt(
    request: OptimizeRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Optimize a single prompt.
    
    Beta mode: API key authentication is optional.
    """
    try:
        # Validate and sanitize
        is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(request.prompt)
        if not is_valid:
            return OptimizeResponse(
                success=False,
                original_prompt=request.prompt,
                error=validation_error
            )

        is_valid_type, prompt_type_enum, type_error = validate_prompt_type(request.prompt_type)
        if not is_valid_type:
            return OptimizeResponse(
                success=False,
                original_prompt=request.prompt,
                error=type_error
            )

        # Beta mode: No usage limits
        # if not db.check_usage_limit(user.id if user else None):
        #     raise HTTPException(
        #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #         detail="Daily usage limit exceeded"
        #     )

        # Optimize
        orchestrator = OrchestratorAgent()
        results = orchestrator.optimize_prompt(sanitized_prompt, prompt_type_enum)

        # Beta mode: Don't track usage
        # db.increment_usage(user.id if user else None)

        # Save session (optional in beta)
        try:
            db.save_session(
                user_id=user.id if user else None,
            original_prompt=sanitized_prompt,
            prompt_type=request.prompt_type,
            optimized_prompt=results.get("optimized_prompt", "")[:1000],
                sample_output=results.get("sample_output", "")[:2000],
                quality_score=results.get("quality_score")
            )
        except Exception:
            pass  # Optional in beta mode

        return OptimizeResponse(
            success=True,
            original_prompt=sanitized_prompt,
            optimized_prompt=results.get("optimized_prompt"),
            quality_score=results.get("quality_score"),
            deconstruction=results.get("deconstruction"),
            diagnosis=results.get("diagnosis"),
            evaluation=results.get("evaluation"),
            sample_output=results.get("sample_output")
        )
    except Exception as e:
        logger.error(f"Error optimizing prompt: {str(e)}")
        return OptimizeResponse(
            success=False,
            original_prompt=request.prompt,
            error=str(e)
        )


@app.post("/api/v1/batch/optimize", response_model=BatchOptimizeResponse)
async def batch_optimize(
    request: BatchOptimizeRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Optimize multiple prompts in batch.
    
    Requires API key authentication.
    """
    try:
        batch_optimizer = BatchOptimizer()
        job = batch_optimizer.create_and_process_batch(
            request.prompts,
            user.id if user else None,
            request.name
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch job"
            )

        return BatchOptimizeResponse(
            job_id=job.id,
            status=job.status,
            total_prompts=job.total_prompts
        )
    except Exception as e:
        logger.error(f"Error creating batch job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/batch/{job_id}")
async def get_batch_job(job_id: int, user: Optional[User] = Depends(get_current_user)):
    """Get batch job status and results."""
    try:
        db_session = db.get_session()
        query = db_session.query(BatchJob).filter(BatchJob.id == job_id)
        # Beta mode: Allow access if user matches or if no user (anonymous)
        if user:
            query = query.filter(BatchJob.user_id == user.id)
        job = query.first()
        db_session.close()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch job not found"
            )

        import json
        results = json.loads(job.results_json) if job.results_json else None

        return {
            "job_id": job.id,
            "name": job.name,
            "status": job.status,
            "total_prompts": job.total_prompts,
            "completed_prompts": job.completed_prompts,
            "failed_prompts": job.failed_prompts,
            "results": results,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    except Exception as e:
        logger.error(f"Error getting batch job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/ab-test/create")
async def create_ab_test(
    request: ABTestRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """Create an A/B test."""
    try:
        ab_testing = ABTesting()
        ab_test = ab_testing.create_test(
            user.id if user else None,
            request.name,
            request.original_prompt,
            request.variant_a,
            request.variant_b
        )

        if not ab_test:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create A/B test"
            )

        return {
            "test_id": ab_test.id,
            "name": ab_test.name,
            "status": ab_test.status
        }
    except Exception as e:
        logger.error(f"Error creating A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/ab-test/{test_id}")
async def get_ab_test_results(test_id: int, user: Optional[User] = Depends(get_current_user)):
    """Get A/B test results."""
    try:
        ab_testing = ABTesting()
        results = ab_testing.get_test_results(test_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test not found"
            )

        return results
    except Exception as e:
        logger.error(f"Error getting A/B test results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/export")
async def export(
    request: ExportRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Export optimization results.
    
    Supports JSON, Markdown, and PDF formats.
    """
    try:
        if request.format == "pdf":
            pdf_buffer = export_results(request.results, "pdf")
            from fastapi.responses import Response
            return Response(
                content=pdf_buffer.read(),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
            )
        else:
            exported = export_results(request.results, request.format)
            return {
                "format": request.format,
                "content": exported
            }
    except Exception as e:
        logger.error(f"Error exporting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/analytics")
async def get_analytics(
    days: int = 30,
    user: Optional[User] = Depends(get_current_user)
):
    """Get user analytics."""
    try:
        from analytics import Analytics
        analytics_data = Analytics.get_user_analytics(user.id if user else None, days)
        return analytics_data
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/user/api-key")
async def get_api_key(user: Optional[User] = Depends(get_current_user)):
    """Get or generate API key for user."""
    try:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account required for API key. Create an account or provide authentication."
            )
        if not user.api_key:
            api_key = db.generate_api_key(user.id)
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate API key"
                )
            return {"api_key": api_key}
        return {"api_key": user.api_key}
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
