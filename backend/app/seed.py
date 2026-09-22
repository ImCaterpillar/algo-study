import json
from sqlalchemy.orm import Session

from .config import CREATE_DEMO_USER, DATA_DIR, DEMO_EMAIL, DEMO_PASSWORD, DEMO_USERNAME
from .models import Problem, Template, User
from .routes.utils import new_progress
from .services.auth_service import get_password_hash

DEFAULT_STARTER_CODE = {
    "python": "def solve(*args):\n    # TODO: implement your solution\n    pass\n",
    "javascript": "function solve(...args) {\n  // TODO: implement your solution\n}\n",
    "java": "class Solution {\n    // TODO: implement your solution\n}\n",
    "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    // TODO: implement your solution\n};\n",
}


def seed_database(db: Session) -> None:
    seed_users(db)
    seed_problems(db)
    seed_templates(db)
    db.commit()


def seed_users(db: Session) -> None:
    """Create the optional demo account for local development only."""
    if not CREATE_DEMO_USER:
        return
    existing_demo = db.query(User).filter(User.username == DEMO_USERNAME).first()
    if existing_demo:
        return
    db.add(
        User(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL.lower(),
            hashed_password=get_password_hash(DEMO_PASSWORD),
        )
    )
    db.flush()


def _read_json_seed(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def seed_problems(db: Session) -> None:
    """Upsert curated problems without touching user progress/submissions."""
    default_user = db.query(User).filter(User.username == DEMO_USERNAME).first()
    for item in _read_json_seed("problems.json"):
        problem = db.get(Problem, item["id"])
        is_new = problem is None
        if is_new:
            problem = Problem(id=item["id"])
            db.add(problem)

        problem.leetcode_id = item.get("leetcode_id")
        problem.title = item["title"]
        problem.title_cn = item.get("title_cn")
        problem.slug = item.get("slug")
        problem.difficulty = item["difficulty"]
        problem.description = item.get("description", "")
        problem.examples = json.dumps(item.get("examples", []), ensure_ascii=False)
        problem.constraints_text = item.get("constraints_text", "")
        problem.tags = json.dumps(item.get("tags", []), ensure_ascii=False)
        problem.stage = item.get("stage")
        problem.source = item.get("source")
        problem.source_url = item.get("source_url")
        problem.key_pattern = item.get("key_pattern", "")
        problem.starter_code = json.dumps(item.get("starter_code", DEFAULT_STARTER_CODE), ensure_ascii=False)
        problem.recommended_order = item.get("recommended_order", item["id"])

        if is_new:
            db.flush()
            if default_user:
                db.add(new_progress(problem_id=problem.id, user_id=default_user.id))


def seed_templates(db: Session) -> None:
    """Upsert system templates while preserving user-owned personal templates."""
    for item in _read_json_seed("templates.json"):
        template_id = item.get("id")
        template = db.get(Template, template_id) if template_id is not None else None
        if template is not None and template.owner_user_id is not None:
            # Do not overwrite a user-owned template if a hand-edited DB happens to reuse
            # a seed ID. Fall back to natural-key lookup or create a fresh system row.
            template = None
        if template is None:
            template = (
                db.query(Template)
                .filter(
                    Template.is_system.is_(True),
                    Template.owner_user_id.is_(None),
                    Template.name == item["name"],
                    Template.category == item["category"],
                    Template.language == item["language"],
                )
                .first()
            )
        if template is None:
            id_is_free = template_id is not None and db.get(Template, template_id) is None
            template = Template(id=template_id) if id_is_free else Template()
            db.add(template)

        template.owner_user_id = None
        template.is_system = True
        template.name = item["name"]
        template.category = item["category"]
        template.language = item["language"]
        template.code = item["code"]
        template.explanation = item.get("explanation", "")
        template.tags = json.dumps(item.get("tags", []), ensure_ascii=False)
        template.usage_scenario = item.get("usage_scenario", "")
