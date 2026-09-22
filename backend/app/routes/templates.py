import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Problem, Template, User
from ..schemas import TemplateCreate, TemplateOut, TemplatePage, TemplateRecommendation, TemplateUpdate
from .auth import get_current_user
from .utils import safe_json_loads

router = APIRouter(prefix="/templates", tags=["templates"])


def _visible_templates_query(db: Session, user_id: int):
    return db.query(Template).filter(
        or_(Template.is_system.is_(True), Template.owner_user_id == user_id)
    )


def _template_to_out(template: Template) -> TemplateOut:
    return TemplateOut(
        id=template.id,
        owner_user_id=template.owner_user_id,
        is_system=bool(template.is_system),
        name=template.name,
        category=template.category,
        language=template.language,
        code=template.code,
        explanation=template.explanation or "",
        tags=safe_json_loads(template.tags, []),
        usage_scenario=template.usage_scenario or "",
    )


def _get_visible_template(db: Session, template_id: int, user_id: int) -> Template:
    template = _visible_templates_query(db, user_id).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


def _ensure_personal_template(template: Template) -> None:
    if template.is_system or template.owner_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System templates are read-only. Copy it into a personal template before editing.",
        )


@router.get("", response_model=TemplatePage)
def list_templates(
    language: str | None = Query(default=None),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _visible_templates_query(db, current_user.id)
    if language:
        query = query.filter(Template.language == language)
    if category:
        query = query.filter(Template.category == category)
    items = query.order_by(Template.is_system.desc(), Template.category.asc(), Template.name.asc(), Template.language.asc()).all()
    if tag:
        items = [t for t in items if tag in safe_json_loads(t.tags, [])]
    total = len(items)
    page_items = items[offset : offset + limit]
    data = [_template_to_out(t) for t in page_items]
    return {
        "items": data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(data) < total,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    templates = _visible_templates_query(db, current_user.id).all()
    return sorted({t.category for t in templates if t.category})


@router.get("/languages")
def list_languages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    templates = _visible_templates_query(db, current_user.id).all()
    return sorted({t.language for t in templates if t.language})


@router.get("/recommend/{problem_id}", response_model=list[TemplateRecommendation])
def recommend_templates(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        return []

    problem_tags = set(safe_json_loads(problem.tags, []))
    templates = _visible_templates_query(db, current_user.id).all()

    recommendations = []
    for template in templates:
        template_tags = set(safe_json_loads(template.tags, []))
        matched_tags = sorted(problem_tags & template_tags)
        if matched_tags:
            total_tags = max(len(problem_tags), len(template_tags), 1)
            match_score = round(len(matched_tags) / total_tags, 2)
            recommendations.append(TemplateRecommendation(
                template_id=template.id,
                name=template.name,
                category=template.category,
                language=template.language,
                explanation=template.explanation or "",
                match_score=match_score,
                matched_tags=matched_tags,
            ))

    return sorted(recommendations, key=lambda x: (-x.match_score, x.name))


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _template_to_out(_get_visible_template(db, template_id, current_user.id))


@router.post("", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(data: TemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = Template(
        owner_user_id=current_user.id,
        is_system=False,
        name=data.name.strip(),
        category=data.category.strip(),
        language=data.language,
        code=data.code,
        explanation=data.explanation,
        tags=json.dumps(data.tags, ensure_ascii=False),
        usage_scenario=data.usage_scenario,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_out(template)


@router.post("/{template_id}/copy", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def copy_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    source = _get_visible_template(db, template_id, current_user.id)
    template = Template(
        owner_user_id=current_user.id,
        is_system=False,
        name=f"{source.name}（副本）",
        category=source.category,
        language=source.language,
        code=source.code,
        explanation=source.explanation or "",
        tags=source.tags or "[]",
        usage_scenario=source.usage_scenario or "",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_out(template)


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(template_id: int, data: TemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = _get_visible_template(db, template_id, current_user.id)
    _ensure_personal_template(template)

    if data.name is not None:
        template.name = data.name.strip()
    if data.category is not None:
        template.category = data.category.strip()
    if data.language is not None:
        template.language = data.language
    if data.code is not None:
        template.code = data.code
    if data.explanation is not None:
        template.explanation = data.explanation
    if data.tags is not None:
        template.tags = json.dumps(data.tags, ensure_ascii=False)
    if data.usage_scenario is not None:
        template.usage_scenario = data.usage_scenario

    db.commit()
    db.refresh(template)
    return _template_to_out(template)


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = _get_visible_template(db, template_id, current_user.id)
    _ensure_personal_template(template)

    db.delete(template)
    db.commit()
    return {"success": True, "message": "Template deleted"}
