from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

Language = Literal["python", "javascript", "java", "cpp"]
SubmissionStatus = Literal[
    "Not Started",
    "Accepted",
    "Wrong Answer",
    "Runtime Error",
    "Compile Error",
    "Timeout",
    "Need Review",
    "Attempted",
]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class ProgressOut(BaseModel):
    status: str = "Not Started"
    attempts: int = 0
    mastery_level: int = 0
    confidence: int = 0
    is_favorite: bool = False
    next_review_at: Optional[datetime] = None

class ProblemListItem(BaseModel):
    id: int
    leetcode_id: Optional[int] = None
    title: str
    title_cn: Optional[str] = None
    difficulty: str
    tags: list[str] = Field(default_factory=list)
    stage: Optional[str] = None
    source_url: Optional[str] = None
    recommended_order: int = 0
    progress: Optional[ProgressOut] = None



class ProblemPage(BaseModel):
    items: list[ProblemListItem]
    total: int
    limit: int
    offset: int
    has_more: bool

class ProblemDetail(ProblemListItem):
    description: Optional[str] = None
    examples: list[dict[str, Any]] = Field(default_factory=list)
    constraints_text: Optional[str] = None
    key_pattern: Optional[str] = None
    starter_code: dict[str, str] = Field(default_factory=dict)

class SubmissionCreate(BaseModel):
    problem_id: int
    language: Language
    code: str = Field(min_length=1, max_length=200_000)
    status: SubmissionStatus
    fail_reason: Optional[str] = Field(default=None, max_length=100)
    error_message: Optional[str] = Field(default=None, max_length=10_000)
    runtime_ms: Optional[int] = Field(default=None, ge=0)
    memory_mb: Optional[float] = Field(default=None, ge=0)
    is_best: bool = False
    mastery_level: Optional[int] = Field(default=None, ge=0, le=5)
    confidence: Optional[int] = Field(default=None, ge=0, le=5)

class SubmissionOut(BaseModel):
    id: int
    problem_id: int
    language: str
    code: str
    status: str
    runtime_ms: Optional[int] = None
    memory_mb: Optional[float] = None
    error_message: Optional[str] = None
    fail_reason: Optional[str] = None
    is_best: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}



class SubmissionPage(BaseModel):
    items: list[SubmissionOut]
    total: int
    limit: int
    offset: int
    has_more: bool

class NoteUpdate(BaseModel):
    idea: str = Field(default="", max_length=20_000)
    key_points: str = Field(default="", max_length=20_000)
    complexity: str = Field(default="", max_length=5_000)
    pitfalls: str = Field(default="", max_length=20_000)
    summary: str = Field(default="", max_length=20_000)

class NoteOut(NoteUpdate):
    id: Optional[int] = None
    problem_id: int

    model_config = {"from_attributes": True}

class ProgressUpdate(BaseModel):
    status: Optional[SubmissionStatus] = None
    mastery_level: Optional[int] = Field(default=None, ge=0, le=5)
    confidence: Optional[int] = Field(default=None, ge=0, le=5)
    is_favorite: Optional[bool] = None

ReviewResult = Literal["掌握", "部分遗忘", "完全遗忘", ""]

class ReviewCreate(BaseModel):
    problem_id: int
    review_type: str = Field(default="Manual", max_length=50)
    result: ReviewResult = ""
    notes: str = Field(default="", max_length=20_000)
    mastery_level: Optional[int] = Field(default=None, ge=0, le=5)


class QuickReviewCreate(BaseModel):
    problem_id: int
    result: Literal["掌握", "部分遗忘", "完全遗忘"]

class ReviewLogOut(BaseModel):
    id: int
    problem_id: int
    review_type: str
    result: str
    notes: str
    prev_mastery_level: int
    new_mastery_level: int
    review_interval_days: int
    created_at: datetime

    model_config = {"from_attributes": True}

class ReviewPlanOut(BaseModel):
    problem_id: int
    title: str
    title_cn: Optional[str]
    difficulty: str
    mastery_level: int
    next_review_at: Optional[datetime]
    review_due: str
    total_reviews: int



class ReviewPlanPage(BaseModel):
    items: list[ReviewPlanOut]
    total: int
    limit: int
    offset: int
    has_more: bool


class ReviewLogPage(BaseModel):
    items: list[ReviewLogOut]
    total: int
    limit: int
    offset: int
    has_more: bool

class FailReasonTrend(BaseModel):
    fail_reason: str
    count: int
    percentage: float

class TemplateOut(BaseModel):
    id: int
    owner_user_id: Optional[int] = None
    is_system: bool = False
    name: str
    category: str
    language: str
    code: str
    explanation: str
    tags: list[str] = Field(default_factory=list)
    usage_scenario: str



class TemplatePage(BaseModel):
    items: list[TemplateOut]
    total: int
    limit: int
    offset: int
    has_more: bool

class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    language: Language
    code: str = Field(min_length=1, max_length=200_000)
    explanation: str = Field(default="", max_length=20_000)
    tags: list[str] = Field(default_factory=list, max_length=50)
    usage_scenario: str = Field(default="", max_length=20_000)

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    language: Optional[Language] = None
    code: Optional[str] = Field(default=None, min_length=1, max_length=200_000)
    explanation: Optional[str] = Field(default=None, max_length=20_000)
    tags: Optional[list[str]] = Field(default=None, max_length=50)
    usage_scenario: Optional[str] = Field(default=None, max_length=20_000)

class TemplateRecommendation(BaseModel):
    template_id: int
    name: str
    category: str
    language: str
    explanation: str
    match_score: float
    matched_tags: list[str] = Field(default_factory=list)

class PracticeProblem(BaseModel):
    id: int
    title: str
    title_cn: Optional[str]
    difficulty: str
    tags: list[str] = Field(default_factory=list)
    template_id: int
    template_name: str
    expected_pattern: str

class StatsSummary(BaseModel):
    total_problems: int
    attempted: int
    accepted: int
    need_review: int
    average_mastery: float
    by_difficulty: dict[str, dict[str, int]]
    by_tag: dict[str, dict[str, float]]
    fail_reason_trends: list[FailReasonTrend] = Field(default_factory=list)
