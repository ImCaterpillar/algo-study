from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Problem, Progress, User
from ..schemas import ProblemDetail, ProblemPage, ProgressUpdate
from .utils import new_progress, problem_to_detail, problem_to_list_item, progress_to_out, safe_json_loads
from .auth import get_current_user

router = APIRouter(prefix="/problems", tags=["problems"])

@router.get("", response_model=ProblemPage)
def list_problems(
    difficulty: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Problem, Progress)
        .outerjoin(Progress, (Progress.problem_id == Problem.id) & (Progress.user_id == current_user.id))
    )
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    if stage:
        query = query.filter(Problem.stage == stage)
    if status:
        if status == "Not Started":
            query = query.filter(or_(Progress.id.is_(None), Progress.status == "Not Started"))
        else:
            query = query.filter(Progress.status == status)
    rows = query.order_by(Problem.recommended_order.asc()).all()
    if tag:
        rows = [(problem, progress) for problem, progress in rows if tag in safe_json_loads(problem.tags, [])]
    total = len(rows)
    page_rows = rows[offset : offset + limit]
    items = [problem_to_list_item(problem, progress=progress) for problem, progress in page_rows]
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }

@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = db.query(Progress).filter(Progress.problem_id == problem_id, Progress.user_id == current_user.id).first()
    return problem_to_detail(problem, progress=progress)

@router.patch("/{problem_id}/progress")
def update_progress(problem_id: int, payload: ProgressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = db.query(Progress).filter(Progress.problem_id == problem_id, Progress.user_id == current_user.id).first()
    if not progress:
        progress = new_progress(problem_id=problem_id, user_id=current_user.id)
        db.add(progress)
    if payload.status is not None:
        progress.status = payload.status
    if payload.mastery_level is not None:
        progress.mastery_level = payload.mastery_level
    if payload.confidence is not None:
        progress.confidence = payload.confidence
    if payload.is_favorite is not None:
        progress.is_favorite = payload.is_favorite
    db.commit()
    db.refresh(progress)
    return {"ok": True, "progress": progress_to_out(progress)}
