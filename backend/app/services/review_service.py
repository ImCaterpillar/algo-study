from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Problem, Progress, ReviewLog

INTERVALS = {
    0: 1,
    1: 1,
    2: 3,
    3: 7,
    4: 14,
    5: 30,
}

REVIEW_TYPES = ["D+1", "D+3", "D+7", "D+14", "D+30"]

def get_interval_days(mastery_level: int) -> int:
    return INTERVALS.get(mastery_level, 1)

def next_review_date(mastery_level: int | None) -> datetime:
    level = mastery_level or 0
    days = get_interval_days(level)
    return datetime.utcnow() + timedelta(days=days)

def calculate_review_interval(progress: Progress) -> int:
    if not progress.last_review_at:
        return 0
    delta = datetime.utcnow() - progress.last_review_at
    return delta.days

def update_mastery_after_review(progress: Progress, result: str, review_interval: int) -> int:
    prev_level = progress.mastery_level
    expected_interval = get_interval_days(prev_level)
    if result == "掌握":
        if review_interval >= expected_interval:
            new_level = min(prev_level + 1, 5)
        else:
            new_level = prev_level
    elif result == "部分遗忘":
        new_level = max(prev_level - 1, 0)
    elif result == "完全遗忘":
        new_level = max(prev_level - 2, 0)
    else:
        new_level = prev_level
    return new_level

def get_review_plan(db: Session, problem_id: int, user_id: int) -> dict:
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        return None
    progress = db.query(Progress).filter(Progress.problem_id == problem_id, Progress.user_id == user_id).first()
    review_logs = (
        db.query(ReviewLog)
        .filter(ReviewLog.problem_id == problem_id, ReviewLog.user_id == user_id)
        .order_by(ReviewLog.created_at.desc())
        .all()
    )
    review_due = "已到期"
    if progress and progress.next_review_at:
        if progress.next_review_at > datetime.utcnow():
            delta = (progress.next_review_at - datetime.utcnow()).days
            review_due = f"还有{delta}天"
        else:
            review_due = "已到期"
    return {
        "problem_id": problem_id,
        "title": problem.title,
        "title_cn": problem.title_cn,
        "difficulty": problem.difficulty,
        "mastery_level": progress.mastery_level if progress else 0,
        "next_review_at": progress.next_review_at if progress else None,
        "review_due": review_due,
        "total_reviews": len(review_logs),
    }

def get_due_reviews(db: Session, user_id: int) -> list[dict]:
    now = datetime.utcnow()
    problems = (
        db.query(Problem)
        .outerjoin(Progress, (Progress.problem_id == Problem.id) & (Progress.user_id == user_id))
        .filter(
            ((Progress.status == "Need Review") |
            (Progress.mastery_level < 3) |
            ((Progress.next_review_at.isnot(None)) & (Progress.next_review_at <= now))) |
            (Progress.id.is_(None))
        )
        .order_by(Progress.next_review_at.asc().nullsfirst(), Problem.recommended_order.asc())
        .all()
    )
    return [get_review_plan(db, p.id, user_id) for p in problems]

def create_review_log(
    db: Session,
    user_id: int,
    problem_id: int,
    review_type: str,
    result: str,
    notes: str = "",
    new_mastery_level: int | None = None,
) -> ReviewLog:
    progress = db.query(Progress).filter(Progress.problem_id == problem_id, Progress.user_id == user_id).first()
    if not progress:
        return None
    prev_level = progress.mastery_level
    review_interval = calculate_review_interval(progress)
    if new_mastery_level is None:
        new_level = update_mastery_after_review(progress, result, review_interval)
    else:
        new_level = new_mastery_level
    log = ReviewLog(
        user_id=user_id,
        problem_id=problem_id,
        review_type=review_type,
        result=result,
        notes=notes,
        prev_mastery_level=prev_level,
        new_mastery_level=new_level,
        review_interval_days=review_interval,
    )
    db.add(log)
    progress.last_review_at = datetime.utcnow()
    progress.mastery_level = new_level
    if new_level >= 3 and progress.status == "Need Review":
        progress.status = "Attempted"
    progress.next_review_at = next_review_date(new_level)
    db.commit()
    db.refresh(log)
    return log

def get_review_history(
    db: Session,
    problem_id: int | None = None,
    user_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ReviewLog]:
    query = db.query(ReviewLog)
    if user_id:
        query = query.filter(ReviewLog.user_id == user_id)
    if problem_id:
        query = query.filter(ReviewLog.problem_id == problem_id)
    return query.order_by(ReviewLog.created_at.desc()).offset(offset).limit(limit).all()

def get_problems_by_review_schedule(db: Session, days: int, user_id: int) -> list[dict]:
    target_date = datetime.utcnow() + timedelta(days=days)
    problems = (
        db.query(Problem)
        .outerjoin(Progress, (Progress.problem_id == Problem.id) & (Progress.user_id == user_id))
        .filter(
            (Progress.next_review_at.isnot(None)) &
            (Progress.next_review_at <= target_date) &
            (Progress.next_review_at > datetime.utcnow())
        )
        .all()
    )
    return [get_review_plan(db, p.id, user_id) for p in problems]