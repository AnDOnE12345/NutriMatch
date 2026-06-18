from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models import User, Supplement, Recommendation
from backend.schemas import SupplementResponse, RecommendationResponse
from backend.routes.auth_routes import get_current_user
from backend.services.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/api", tags=["supplements"])


@router.get("/supplements", response_model=list[SupplementResponse])
def list_supplements(
    category: Optional[str] = None,
    form: Optional[str] = None,
    is_vegan: Optional[bool] = None,
    is_organic: Optional[bool] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Supplement)

    if category:
        query = query.filter(Supplement.category == category)
    if form:
        query = query.filter(Supplement.form == form)
    if is_vegan is not None:
        query = query.filter(Supplement.is_vegan == is_vegan)
    if is_organic is not None:
        query = query.filter(Supplement.is_organic == is_organic)
    if max_price is not None:
        query = query.filter(Supplement.price <= max_price)
    if search:
        query = query.filter(Supplement.name.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()


@router.get("/supplements/{supplement_id}", response_model=SupplementResponse)
def get_supplement(supplement_id: int, db: Session = Depends(get_db)):
    supplement = db.query(Supplement).filter(Supplement.id == supplement_id).first()
    if not supplement:
        raise HTTPException(status_code=404, detail="Supplement not found")
    return supplement


@router.post("/recommendations/generate", response_model=RecommendationResponse)
def create_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recommendation = generate_recommendations(current_user, db)
    return recommendation


@router.get("/recommendations/my", response_model=list[RecommendationResponse])
def get_my_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(10)
        .all()
    )
