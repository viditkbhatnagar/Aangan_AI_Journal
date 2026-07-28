"""Shared wording safety: the never-medical boundary, enforced in CODE.

Any agent that writes user-facing care wording (Alerter, PersonalRadar,
Reflector) must reject clinical-sounding LLM output and fall back to its
deterministic template. One regex, one place — never copy-pasted.
"""
import re

MEDICAL_RE = re.compile(
    r"\b(diagnos\w*|prescri\w*|medicat\w*|dosage|symptom\w*|clinical|disease\w*|"
    r"treatment\w*|therap\w*|doctor should|see a doctor immediately|emergency room)\b",
    re.I,
)


def sounds_medical(text: str) -> bool:
    return bool(MEDICAL_RE.search(text or ""))
