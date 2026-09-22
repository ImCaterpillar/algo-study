from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from ..models import Problem, Progress, Submission, ReviewLog
from ..routes.utils import problem_to_list_item, safe_json_loads

def calculate_weakness_score(db: Session, user_id: int) -> dict:
    """计算每个标签的弱项分数：基于错误次数、未通过率、掌握度"""
    submissions = db.query(Submission).filter(Submission.user_id == user_id).all()
    progress_by_problem = {p.problem_id: p for p in db.query(Progress).filter(Progress.user_id == user_id).all()}
    problems = db.query(Problem).all()
    problem_tags = {p.id: safe_json_loads(p.tags, []) for p in problems}

    tag_stats = defaultdict(lambda: {
        "total": 0,
        "failed": 0,
        "need_review": 0,
        "mastery_sum": 0,
        "avg_mastery": 0.0,
        "weakness_score": 0.0,
    })

    for problem in problems:
        tags = problem_tags.get(problem.id, [])
        progress = progress_by_problem.get(problem.id)
        for tag in tags:
            tag_stats[tag]["total"] += 1
            if progress:
                tag_stats[tag]["mastery_sum"] += progress.mastery_level
                if progress.status == "Need Review" or progress.mastery_level < 3:
                    tag_stats[tag]["need_review"] += 1

    for tag, stats in tag_stats.items():
        total = stats["total"] or 1
        stats["avg_mastery"] = round(stats["mastery_sum"] / total, 2)
        need_review_rate = stats["need_review"] / total
        mastery_gap = (3 - stats["avg_mastery"]) / 3
        stats["weakness_score"] = round(need_review_rate * 0.6 + mastery_gap * 0.4, 3)

    weakness_list = sorted(tag_stats.items(), key=lambda x: -x[1]["weakness_score"])
    strongest_list = sorted(
        tag_stats.items(),
        key=lambda x: (x[1]["avg_mastery"], -x[1]["need_review"], x[1]["total"]),
        reverse=True,
    )
    return {
        "by_tag": {tag: stats for tag, stats in weakness_list},
        "weakest_tags": [tag for tag, _ in weakness_list[:5]],
        "strongest_tags": [tag for tag, _ in strongest_list[:5]],
    }

def get_personalized_recommendations(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    """阶段3智能推荐：基于弱项标签优先推荐"""
    weakness_data = calculate_weakness_score(db, user_id)
    weakest_tags = set(weakness_data["weakest_tags"])
    progress_by_problem = {p.problem_id: p for p in db.query(Progress).filter(Progress.user_id == user_id).all()}
    problems = db.query(Problem).all()

    scored_problems = []
    for problem in problems:
        progress = progress_by_problem.get(problem.id)
        if progress and progress.status == "Accepted" and progress.mastery_level >= 4:
            continue
        tags = safe_json_loads(problem.tags, [])
        tag_match_score = sum(1 for t in tags if t in weakest_tags)
        mastery = progress.mastery_level if progress else 0
        urgency = 1.0 if mastery < 2 else 0.5 if mastery < 3 else 0.2
        final_score = tag_match_score * 10 + urgency * 5 + (5 - mastery) * 2
        scored_problems.append((problem, final_score))

    scored_problems.sort(key=lambda x: -x[1])
    chosen = scored_problems[:limit]
    return [problem_to_list_item(problem, progress=progress_by_problem.get(problem.id)) for problem, _ in chosen]

def get_today_recommendations(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    """每日推荐：混合未开始题、待复盘题和弱项相关题"""
    weakness_data = calculate_weakness_score(db, user_id)
    weakest_tags = set(weakness_data["weakest_tags"])
    progress_by_problem = {p.problem_id: p for p in db.query(Progress).filter(Progress.user_id == user_id).all()}
    problems = db.query(Problem).all()

    not_started = []
    need_review = []
    weakness_related = []

    for problem in problems:
        progress = progress_by_problem.get(problem.id)
        tags = set(safe_json_loads(problem.tags, []))

        if not progress or progress.status == "Not Started":
            not_started.append(problem)
        elif progress.status == "Need Review" or progress.mastery_level < 3:
            need_review.append(problem)

        if tags & weakest_tags and (not progress or progress.mastery_level < 4):
            weakness_related.append((problem, len(tags & weakest_tags)))

    weakness_related.sort(key=lambda x: -x[1])
    weakness_problems = [p[0] for p in weakness_related[:3]]

    result_set = []
    for p in not_started[:limit]:
        if p not in result_set:
            result_set.append(p)
    for p in need_review[:limit]:
        if p not in result_set:
            result_set.append(p)
    for p in weakness_problems:
        if p not in result_set and len(result_set) < limit * 2:
            result_set.append(p)

    return [problem_to_list_item(p, progress=progress_by_problem.get(p.id)) for p in result_set[:limit]]

def generate_weekly_report(db: Session, user_id: int) -> dict:
    """生成周报：总结本周学习情况"""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    submissions_this_week = db.query(Submission).filter(Submission.user_id == user_id, Submission.created_at >= week_ago).all()
    reviews_this_week = db.query(ReviewLog).filter(ReviewLog.user_id == user_id, ReviewLog.created_at >= week_ago).all()
    all_submissions = db.query(Submission).filter(Submission.user_id == user_id, Submission.created_at >= month_ago).all()

    submissions_by_day = defaultdict(int)
    for sub in submissions_this_week:
        day_key = sub.created_at.strftime("%Y-%m-%d")
        submissions_by_day[day_key] += 1

    review_results = defaultdict(int)
    for log in reviews_this_week:
        review_results[log.result or "未知"] += 1

    fail_reasons = defaultdict(int)
    for sub in all_submissions:
        if sub.fail_reason:
            fail_reasons[sub.fail_reason] += 1

    submitted_problems = len(set(s.problem_id for s in submissions_this_week))
    reviewed_problems = len(set(r.problem_id for r in reviews_this_week))
    accepted_this_week = sum(1 for s in submissions_this_week if s.status == "Accepted")

    return {
        "generated_at": now.isoformat(),
        "period": f"{week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        "submissions_count": len(submissions_this_week),
        "unique_problems_attempted": submitted_problems,
        "accepted_count": accepted_this_week,
        "reviews_count": len(reviews_this_week),
        "unique_problems_reviewed": reviewed_problems,
        "daily_submissions": dict(submissions_by_day),
        "review_results": dict(review_results),
        "top_fail_reasons": dict(sorted(fail_reasons.items(), key=lambda x: -x[1])[:5]),
    }

def get_tag_mastery_radar(db: Session, user_id: int) -> list[dict]:
    """获取标签掌握度雷达图数据"""
    problems = db.query(Problem).all()
    progress_by_problem = {p.problem_id: p for p in db.query(Progress).filter(Progress.user_id == user_id).all()}
    problem_tags = {p.id: safe_json_loads(p.tags, []) for p in problems}

    tag_data = defaultdict(lambda: {"total": 0, "mastery_sum": 0, "accepted": 0})

    for problem in problems:
        tags = problem_tags.get(problem.id, [])
        progress = progress_by_problem.get(problem.id)
        for tag in tags:
            tag_data[tag]["total"] += 1
            if progress:
                tag_data[tag]["mastery_sum"] += progress.mastery_level
                if progress.status == "Accepted":
                    tag_data[tag]["accepted"] += 1

    result = []
    for tag, stats in tag_data.items():
        total = stats["total"] or 1
        completion_rate = stats["accepted"] / total
        avg_mastery = stats["mastery_sum"] / total
        result.append({
            "tag": tag,
            "total_problems": stats["total"],
            "accepted": stats["accepted"],
            "completion_rate": round(completion_rate * 100, 1),
            "avg_mastery": round(avg_mastery, 2),
            "mastery_level": round(avg_mastery / 5 * 100, 1),
        })

    return sorted(result, key=lambda x: x["avg_mastery"])