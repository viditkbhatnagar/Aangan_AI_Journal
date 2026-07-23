"""Append-only audit writes. Guarded like metering: auditing must never break
the product, and application code never edits or deletes audit rows."""


def record(
    actor_id: int | None,
    event: str,
    object_type: str | None = None,
    object_id: int | None = None,
    detail: dict | None = None,
) -> None:
    try:
        import db as db_module
        from models import AuditEvent

        session = db_module.SessionLocal()
        try:
            session.add(AuditEvent(
                actor_id=actor_id,
                event=event,
                object_type=object_type,
                object_id=object_id,
                detail=detail or {},
            ))
            session.commit()
        finally:
            session.close()
    except Exception:
        pass
