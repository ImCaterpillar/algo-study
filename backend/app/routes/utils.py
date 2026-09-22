import ast
import json
from datetime import datetime, timedelta
from typing import Any
from ..models import Problem, Progress
from ..schemas import ProgressOut


def safe_json_loads(value: str | None, default: Any):
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, type(default)) else default
    except json.JSONDecodeError:
        # Earlier template writes used Python's list repr (single quotes).
        # Keep reading those rows while new writes use valid JSON.
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, type(default)) else default
        except (ValueError, SyntaxError):
            return default


def progress_to_out(progress: Progress | None) -> ProgressOut | None:
    if progress is None:
        return None
    return ProgressOut(
        status=progress.status or "Not Started",
        attempts=progress.attempts or 0,
        mastery_level=progress.mastery_level or 0,
        confidence=progress.confidence or 0,
        is_favorite=bool(progress.is_favorite),
        next_review_at=progress.next_review_at,
    )


def _progress_for_user(problem: Problem, user_id: int | None) -> Progress | None:
    if not user_id:
        return None
    progress_items = getattr(problem, "progress", None)
    if not progress_items:
        return None
    if isinstance(progress_items, list):
        for p in progress_items:
            if p.user_id == user_id:
                return p
    elif progress_items.user_id == user_id:
        return progress_items
    return None


def problem_to_list_item(problem: Problem, user_id: int | None = None, progress: Progress | None = None):
    user_progress = progress if progress is not None else _progress_for_user(problem, user_id)
    return {
        "id": problem.id,
        "leetcode_id": problem.leetcode_id,
        "title": problem.title,
        "title_cn": problem.title_cn,
        "difficulty": problem.difficulty,
        "tags": safe_json_loads(problem.tags, []),
        "stage": problem.stage,
        "source_url": problem.source_url,
        "recommended_order": problem.recommended_order,
        "progress": progress_to_out(user_progress),
    }


def problem_to_detail(problem: Problem, user_id: int | None = None, progress: Progress | None = None):
    data = problem_to_list_item(problem, user_id=user_id, progress=progress)
    data.update({
        "description": problem.description,
        "examples": safe_json_loads(problem.examples, []),
        "constraints_text": problem.constraints_text,
        "key_pattern": problem.key_pattern,
        "starter_code": safe_json_loads(problem.starter_code, {}),
    })
    return data


def next_review_date(mastery_level: int | None):
    level = mastery_level or 0
    if level <= 1:
        days = 1
    elif level == 2:
        days = 3
    elif level == 3:
        days = 7
    elif level == 4:
        days = 14
    else:
        days = 30
    return datetime.utcnow() + timedelta(days=days)


def new_progress(problem_id: int, user_id: int) -> Progress:
    return Progress(
        problem_id=problem_id,
        user_id=user_id,
        status="Not Started",
        attempts=0,
        solved_count=0,
        mastery_level=0,
        confidence=0,
        is_favorite=False,
        is_archived=False,
    )
