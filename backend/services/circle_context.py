"""Active-circle request context.

A middleware in app.py stores the raw X-Circle-Id header value here;
auth.get_user_circle_id validates it against a real membership before
honoring it. Outside a request (scripts, background jobs) the value is
None and callers fall back to the user's oldest membership.
"""
from contextvars import ContextVar

requested_circle_id: ContextVar[int | None] = ContextVar(
    "requested_circle_id", default=None
)
