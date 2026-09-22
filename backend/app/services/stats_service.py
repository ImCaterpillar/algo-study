from collections import defaultdict
from sqlalchemy.orm import Session
from ..models import Problem, Progress, Submission
from ..routes.utils import safe_json_loads

def calculate_summary(db: Session, user_id: int) -> dict:
    problems = db.query(Problem).all()
    progress_by_problem = {p.problem_id: p for p in db.query(Progress).filter(Progress.user_id == user_id).all()}
    total = len(problems)
    attempted = 0
    accepted = 0
    need_review = 0
    mastery_sum = 0

    by_difficulty = defaultdict(lambda: {"total": 0, "accepted": 0, "need_review": 0})
    tag_stats = defaultdict(lambda: {"total": 0, "accepted": 0, "mastery_sum": 0})

    for problem in problems:
        progress = progress_by_problem.get(problem.id)
        tags = safe_json_loads(problem.tags, [])
        diff = problem.difficulty
        by_difficulty[diff]["total"] += 1
        if progress:
            mastery_sum += progress.mastery_level
            if progress.attempts > 0 or progress.status != "Not Started":
                attempted += 1
            if progress.status == "Accepted":
                accepted += 1
                by_difficulty[diff]["accepted"] += 1
            if progress.status == "Need Review" or progress.mastery_level < 3:
                need_review += 1
                by_difficulty[diff]["need_review"] += 1
        for tag in tags:
            tag_stats[tag]["total"] += 1
            if progress and progress.status == "Accepted":
                tag_stats[tag]["accepted"] += 1
            if progress:
                tag_stats[tag]["mastery_sum"] += progress.mastery_level

    by_tag = {}
    for tag, stat in tag_stats.items():
        total_tag = stat["total"] or 1
        by_tag[tag] = {
            "total": stat["total"],
            "accepted": stat["accepted"],
            "completion_rate": round(stat["accepted"] / total_tag, 3),
            "average_mastery": round(stat["mastery_sum"] / total_tag, 2),
        }

    fail_reason_trends = calculate_fail_reason_trends(db, user_id)

    return {
        "total_problems": total,
        "attempted": attempted,
        "accepted": accepted,
        "need_review": need_review,
        "average_mastery": round(mastery_sum / total, 2) if total else 0,
        "by_difficulty": dict(by_difficulty),
        "by_tag": by_tag,
        "fail_reason_trends": fail_reason_trends,
    }

def calculate_fail_reason_trends(db: Session, user_id: int, days: int = 30) -> list[dict]:
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    submissions = (
        db.query(Submission)
        .filter(
            Submission.user_id == user_id,
            Submission.fail_reason.isnot(None),
            Submission.fail_reason != "",
            Submission.created_at >= cutoff,
        )
        .all()
    )
    fail_reason_counts = defaultdict(int)
    total_failures = 0
    for sub in submissions:
        if sub.fail_reason:
            fail_reason_counts[sub.fail_reason] += 1
            total_failures += 1
    trends = []
    for reason, count in sorted(fail_reason_counts.items(), key=lambda x: -x[1]):
        percentage = round(count / total_failures * 100, 1) if total_failures > 0 else 0
        trends.append({
            "fail_reason": reason,
            "count": count,
            "percentage": percentage,
        })
    return trends

def get_mastery_distribution(db: Session, user_id: int) -> list[dict]:
    progress_list = db.query(Progress).filter(Progress.user_id == user_id).all()
    distribution = defaultdict(int)
    for p in progress_list:
        distribution[p.mastery_level] += 1
    return [{"level": k, "count": v} for k, v in sorted(distribution.items())]

def get_review_effectiveness(db: Session, user_id: int) -> dict:
    from ..models import ReviewLog
    from sqlalchemy import func
    results = (
        db.query(ReviewLog.result, func.count(ReviewLog.id))
        .filter(ReviewLog.user_id == user_id)
        .group_by(ReviewLog.result)
        .all()
    )
    total = sum(r[1] for r in results)
    effectiveness = []
    for result, count in results:
        effectiveness.append({
            "result": result or "未知",
            "count": count,
            "percentage": round(count / total * 100, 1) if total > 0 else 0,
        })
    return {
        "total_reviews": total,
        "breakdown": effectiveness,
    }