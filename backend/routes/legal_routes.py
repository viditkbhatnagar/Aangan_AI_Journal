from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["legal"])

LEGAL_DIR = Path(__file__).resolve().parent.parent / "legal"
POLICY_VERSION = "2026-07-23"

_DOCS = {"privacy": "privacy.md", "terms": "terms.md"}


@router.get("/legal/{doc}", response_class=PlainTextResponse)
def legal_doc(doc: str):
    filename = _DOCS.get(doc)
    if filename is None:
        raise HTTPException(status_code=404, detail="No such document.")
    return (LEGAL_DIR / filename).read_text(encoding="utf-8")
