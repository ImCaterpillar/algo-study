from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..services.ai_service import analyze_problem_difficulty, generate_problem_hints, review_code, generate_explanation
from ..models import User
from ..schemas import Language
from .auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

class AnalyzeRequest(BaseModel):
    description: str = Field(min_length=1, max_length=50_000)
    examples: list = Field(default_factory=list, max_length=20)
    constraints: str = Field(default="", max_length=20_000)
    tags: list[str] = Field(default_factory=list, max_length=50)

class AnalyzeResponse(BaseModel):
    predicted_difficulty: str
    confidence: float
    difficulty_score: int
    factors: list
    suggestion: str

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_problem(request: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    return analyze_problem_difficulty(
        problem_description=request.description,
        examples=request.examples,
        constraints=request.constraints,
    )

class HintsRequest(BaseModel):
    description: str = Field(min_length=1, max_length=50_000)
    examples: list = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=50)

class HintsResponse(BaseModel):
    hints: list[str]

@router.post("/hints", response_model=HintsResponse)
def get_hints(request: HintsRequest, current_user: User = Depends(get_current_user)):
    hints = generate_problem_hints(
        problem_description=request.description,
        examples=request.examples,
        tags=request.tags,
    )
    return {"hints": hints}

class ReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200_000)
    language: Language
    problem_tags: list[str] = Field(default_factory=list, max_length=50)

class ReviewResponse(BaseModel):
    suggestions: list[str]
    warnings: list[str]
    overall_rating: str

@router.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, current_user: User = Depends(get_current_user)):
    return review_code(
        code=request.code,
        language=request.language,
        problem_tags=request.problem_tags,
    )

class ExplainRequest(BaseModel):
    description: str = Field(min_length=1, max_length=50_000)
    tags: list[str] = Field(default_factory=list, max_length=50)

class ExplainResponse(BaseModel):
    explanation: str

@router.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest, current_user: User = Depends(get_current_user)):
    explanation = generate_explanation(
        problem_description=request.description,
        tags=request.tags,
    )
    return {"explanation": explanation}
