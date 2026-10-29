from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = list(db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)))
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "data": n.data,
        }
        for n in rows
    ]


@router.post("/{notification_id}/read")
def mark_read(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(Notification, notification_id)
    if n and n.user_id == user.id:
        n.is_read = True
        db.commit()
    return {"ok": True}
