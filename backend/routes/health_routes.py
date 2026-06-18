from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import User, HealthData
from backend.schemas import HealthDataSubmit
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/health", tags=["health"])


@router.post("/data")
def submit_health_data(
    data: HealthDataSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    health_entry = HealthData(
        user_id=current_user.id,
        source=data.source,
        data_type=data.data_type,
        value=data.value,
        recorded_at=data.recorded_at or datetime.utcnow(),
    )
    db.add(health_entry)
    db.commit()
    db.refresh(health_entry)
    return {"status": "saved", "id": health_entry.id}


@router.get("/data")
def get_my_health_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(HealthData)
        .filter(HealthData.user_id == current_user.id)
        .order_by(HealthData.recorded_at.desc())
        .limit(50)
        .all()
    )
