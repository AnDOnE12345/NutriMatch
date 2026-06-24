from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.config import GEMINI_API_KEY, GROQ_API_KEY, OLLAMA_MODEL
from backend.database import get_db
from backend.models import Supplement
from backend.schemas import ChatRequest
from backend.services.chat_service import ChatServiceError, generate_chat_reply

router = APIRouter(prefix="/api/chat", tags=["chat"])

_requests: dict[str, deque] = defaultdict(deque)
_rate_lock = Lock()


def _check_rate_limit(client_id: str):
    now = monotonic()
    with _rate_lock:
        bucket = _requests[client_id]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 20:
            raise HTTPException(status_code=429, detail="Zu viele Nachrichten. Bitte warte eine Minute.")
        bucket.append(now)


@router.get("/providers")
def provider_status():
    return {
        "providers": [
            {"id": "local", "label": f"Lokal · {OLLAMA_MODEL}", "configured": True},
            {"id": "gemini", "label": "Gemini", "configured": bool(GEMINI_API_KEY)},
            {"id": "groq", "label": "LLaMA · Groq", "configured": bool(GROQ_API_KEY)},
        ]
    }


@router.post("")
async def chat(payload: ChatRequest, request: Request, db: Session = Depends(get_db)):
    _check_rate_limit(request.client.host if request.client else "unknown")
    supplements = db.query(Supplement).all()
    try:
        reply = await generate_chat_reply(payload.provider, payload.message, payload.history, supplements)
    except ChatServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error

    return {
        "reply": reply,
        "provider": payload.provider,
        "disclaimer": "Allgemeine Information – keine medizinische Diagnose oder individuelle Behandlungsempfehlung.",
    }
