"""Audit logging service."""

from datetime import datetime, timezone, timezone

from sqlalchemy.orm import Session

from app.models.models import AuditLog


def write_audit_log(
    db: Session,
    tool_name: str,
    arguments: dict | None = None,
    result: dict | None = None,
    user_id: int | None = None,
    request_id: int | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        request_id=request_id,
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_logs_for_request(db: Session, request_id: int) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.request_id == request_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
