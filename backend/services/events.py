"""First-party product events (AARRR funnel), privacy-conscious by design:
no third-party trackers, only route-level facts about the user's own actions."""


def record_event(user_id: int, name: str, properties: dict | None = None) -> None:
    try:
        import db as db_module
        from models import ProductEvent

        session = db_module.SessionLocal()
        try:
            session.add(ProductEvent(user_id=user_id, name=name, properties=properties or {}))
            session.commit()
        finally:
            session.close()
    except Exception:
        pass  # analytics must never break the product
