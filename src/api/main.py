"""
FastAPI application for Code Review Agents.
Provides REST API endpoints for code review functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from src.config import settings, LLMProvider
from src.agents.orchestrator import Orchestrator
from src.llm.gateway import LLMGateway


# Pydantic models for API
class CodeReviewRequest(BaseModel):
    """Request model for code review."""
    code: str = Field(..., description="Source code to review", max_length=50000)
    language: Optional[str] = Field(None, description="Programming language (optional)")
    parallel: bool = Field(True, description="Run reviews in parallel")
    provider: Optional[str] = Field(None, description="LLM provider override (ollama, claude, openai)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "def hello():\n    print('Hello World')",
                    "language": "python",
                    "parallel": True
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_provider: dict


class ReviewResponse(BaseModel):
    """Response model for code review."""
    status: str
    security_review: Optional[dict] = None
    style_review: Optional[dict] = None
    summary: Optional[dict] = None
    llm_provider: Optional[dict] = None
    error: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered code review system using multiple specialized agents",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check and basic info."""
    gateway = LLMGateway()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        llm_provider=gateway.get_provider_info()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    gateway = LLMGateway()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        llm_provider=gateway.get_provider_info()
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check - verifies LLM connectivity."""
    try:
        gateway = LLMGateway()
        # Quick test to verify LLM is accessible
        response = await gateway.generate("Say 'OK' and nothing else.")
        return {
            "status": "ready",
            "llm_test": "passed" if response else "failed"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM not ready: {str(e)}")


@app.post("/review", response_model=ReviewResponse)
async def review_code(request: CodeReviewRequest):
    """
    Submit code for review by AI agents.
    
    The code will be analyzed by:
    - Security Reviewer: Checks for vulnerabilities
    - Style Reviewer: Checks for best practices
    - Summarizer: Consolidates findings
    """
    try:
        # Create gateway with optional provider override
        llm_gateway = None
        if request.provider:
            try:
                provider = LLMProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {request.provider}. Use 'ollama', 'claude', 'openai', or 'gemini'"
                )
            try:
                llm_gateway = LLMGateway(provider=provider)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        orchestrator = Orchestrator(llm_gateway=llm_gateway)
        
        if request.parallel:
            result = await orchestrator.review_parallel(
                code=request.code,
                language=request.language
            )
        else:
            result = await orchestrator.review(
                code=request.code,
                language=request.language
            )
        
        return ReviewResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/providers")
async def list_providers():
    """List available LLM providers and their configuration."""
    return {
        "current_provider": settings.llm_provider.value,
        "available_providers": {
            "ollama": {
                "configured": True,
                "base_url": settings.ollama_base_url,
                "model": settings.ollama_model
            },
            "claude": {
                "configured": bool(settings.claude_api_key),
                "model": settings.claude_model
            },
            "openai": {
                "configured": bool(settings.openai_api_key),
                "model": settings.openai_model
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
