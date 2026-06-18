from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, QuestionnaireResponse
from backend.schemas import QuestionnaireSubmit
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


@router.post("/submit")
def submit_questionnaire(
    data: QuestionnaireSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update existing or create new
    existing = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.user_id == current_user.id
    ).first()

    if existing:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "id": existing.id}

    questionnaire = QuestionnaireResponse(
        user_id=current_user.id,
        **data.model_dump()
    )
    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)
    return {"status": "created", "id": questionnaire.id}


@router.get("/my")
def get_my_questionnaire(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.user_id == current_user.id
    ).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="No questionnaire found")
    return questionnaire
