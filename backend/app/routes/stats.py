from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import StatsSummary
from ..services.stats_service import (
    calculate_summary,
    get_mastery_distribution,
    get_review_effectiveness,
)
from ..services.recommendation_service import (
    calculate_weakness_score,
    generate_weekly_report,
    get_personalized_recommendations,
    get_tag_mastery_radar,
    get_today_recommendations,
)
from .auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/summary", response_model=StatsSummary)
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_summary(db, current_user.id)

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    weakness = calculate_weakness_score(db, current_user.id)
    return {
        "summary": calculate_summary(db, current_user.id),
        "recommendations": get_today_recommendations(db, current_user.id, limit=5),
        "weakness_analysis": {
            "by_tag": weakness["by_tag"],
            "weakest_tags": weakness["weakest_tags"],
            "strongest_tags": weakness["strongest_tags"],
        },
    }

@router.get("/weakness")
def weakness_analysis(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_weakness_score(db, current_user.id)

@router.get("/weekly-report")
def weekly_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return generate_weekly_report(db, current_user.id)

@router.get("/tag-mastery-radar")
def tag_mastery_radar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_tag_mastery_radar(db, current_user.id)

@router.get("/mastery-distribution")
def mastery_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_mastery_distribution(db, current_user.id)

@router.get("/review-effectiveness")
def review_effectiveness(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_review_effectiveness(db, current_user.id)

@router.get("/personalized-recommendations")
def personalized_recommendations(limit: int = 5, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    limit = max(1, min(limit, 50))
    return get_personalized_recommendations(db, current_user.id, limit=limit)