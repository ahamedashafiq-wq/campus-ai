from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, Notification
from app.models.enums import NotificationType


def audit(db: Session, actor_id: UUID | None, action: str, resource_type: str, resource_id: str | None = None, details: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
    )


def notify(db: Session, user_id: UUID, title: str, body: str, ntype: NotificationType = NotificationType.system, data: dict | None = None) -> None:
    db.add(
        Notification(
            user_id=user_id,
            type=ntype,
            title=title,
            body=body,
            data=data or {},
        )
    )
