from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Problem, Progress, Submission, User
from ..schemas import SubmissionCreate, SubmissionOut, SubmissionPage
from .utils import new_progress, next_review_date
from .auth import get_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])

ACCEPTED_STATUSES = {"Accepted"}
REVIEW_STATUSES = {"Wrong Answer", "Runtime Error", "Compile Error", "Timeout", "Need Review"}

@router.post("", response_model=SubmissionOut)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == payload.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if payload.is_best:
        db.query(Submission).filter(Submission.problem_id == payload.problem_id, Submission.user_id == current_user.id).update({"is_best": False})

    submission = Submission(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        status=payload.status,
        runtime_ms=payload.runtime_ms,
        memory_mb=payload.memory_mb,
        error_message=payload.error_message,
        fail_reason=payload.fail_reason,
        is_best=payload.is_best,
    )
    db.add(submission)

    progress = db.query(Progress).filter(Progress.problem_id == payload.problem_id, Progress.user_id == current_user.id).first()
    if not progress:
        progress = new_progress(problem_id=payload.problem_id, user_id=current_user.id)
        db.add(progress)
    now = datetime.utcnow()
    progress.attempts = progress.attempts or 0
    progress.solved_count = progress.solved_count or 0
    progress.mastery_level = progress.mastery_level or 0
    progress.confidence = progress.confidence or 0
    progress.attempts += 1
    progress.last_attempt_at = now
    if payload.status in ACCEPTED_STATUSES:
        if progress.status != "Accepted":
            progress.first_solved_at = progress.first_solved_at or now
        progress.status = "Accepted"
        progress.solved_count += 1
        progress.next_review_at = next_review_date(payload.mastery_level if payload.mastery_level is not None else progress.mastery_level)
    elif payload.status in REVIEW_STATUSES:
        progress.status = "Need Review"
        progress.next_review_at = next_review_date(1)
    else:
        progress.status = "Attempted"
    if payload.mastery_level is not None:
        progress.mastery_level = payload.mastery_level
    if payload.confidence is not None:
        progress.confidence = payload.confidence

    db.commit()
    db.refresh(submission)
    return submission

@router.get("/problem/{problem_id}", response_model=SubmissionPage)
def list_submissions(
    problem_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    query = db.query(Submission).filter(Submission.problem_id == problem_id, Submission.user_id == current_user.id)
    total = query.count()
    items = (
        query
        .order_by(Submission.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }
