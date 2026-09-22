from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Progress, ReviewLog, User
from ..schemas import QuickReviewCreate, ReviewCreate, ReviewLogOut, ReviewLogPage, ReviewPlanOut, ReviewPlanPage
from ..services.review_service import (
    create_review_log,
    get_due_reviews,
    get_review_history,
    get_review_plan,
    get_problems_by_review_schedule,
)
from .auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.get("/due", response_model=ReviewPlanPage)
def due_reviews(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = get_due_reviews(db, current_user.id)
    total = len(rows)
    items = rows[offset : offset + limit]
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }

@router.get("/plan/{problem_id}", response_model=ReviewPlanOut)
def review_plan(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = get_review_plan(db, problem_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Problem not found")
    return plan

@router.get("/schedule/{days}", response_model=list[ReviewPlanOut])
def review_schedule(days: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if days not in {1, 3, 7, 14, 30}:
        raise HTTPException(status_code=400, detail="Unsupported review schedule")
    return get_problems_by_review_schedule(db, days, current_user.id)

@router.get("/history", response_model=ReviewLogPage)
def review_history(
    problem_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ReviewLog).filter(ReviewLog.user_id == current_user.id)
    if problem_id is not None:
        query = query.filter(ReviewLog.problem_id == problem_id)
    total = query.count()
    items = get_review_history(db, problem_id, current_user.id, limit=limit, offset=offset)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }

@router.post("/log", response_model=ReviewLogOut)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = create_review_log(
        db,
        user_id=current_user.id,
        problem_id=payload.problem_id,
        review_type=payload.review_type,
        result=payload.result,
        notes=payload.notes,
        new_mastery_level=payload.mastery_level,
    )
    if not log:
        raise HTTPException(status_code=404, detail="Progress not found")
    return log

@router.post("/quick-review", response_model=ReviewLogOut)
def quick_review(payload: QuickReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem_id = payload.problem_id
    result = payload.result
    progress = db.query(Progress).filter(Progress.problem_id == problem_id, Progress.user_id == current_user.id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    log = create_review_log(
        db,
        user_id=current_user.id,
        problem_id=problem_id,
        review_type="Quick",
        result=result,
        notes="",
        new_mastery_level=None,
    )
    if not log:
        raise HTTPException(status_code=404, detail="Progress not found")
    return log
