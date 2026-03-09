"""
AI integration — Google Gemini via the new google-genai SDK (gemini-2.0-flash).

Returns a dict with:
  cv_adaptado, cover_letter, keywords_encontradas, keywords_faltando,
  sugestoes, score, cargo_identificado, empresa_identificada
"""
import json
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)

_RETRY_STATUSES = {503, 429}  # UNAVAILABLE or RESOURCE_EXHAUSTED
_MAX_RETRIES = 4
_BACKOFF_BASE = 2  # seconds

PROMPT_TEMPLATE = """You are an expert career coach and professional CV writer.
Analyse the candidate's CV against the Job Description below and return ONLY a valid JSON object.
Do NOT include markdown, code blocks, backticks, or any text outside the JSON.

CV:
--- CV START ---
{cv_text}
--- CV END ---

Job Description:
--- JD START ---
{job_description}
--- JD END ---

Return exactly this JSON structure (no extra fields, no comments):
{{
  "cv_adaptado": "<full rewritten CV text in the same language as the original CV, tailored for this JD>",
  "cover_letter": "<full professional cover letter in the same language as the original CV, 3-4 paragraphs>",
  "linkedin_message": "<LinkedIn connection request message to the recruiter, max 300 characters, in the same language as the original CV, friendly and specific to this JD>",
  "keywords_encontradas": ["<keyword present in both CV and JD>"],
  "keywords_faltando": ["<important keyword from JD missing from CV>"],
  "sugestoes": ["<specific actionable improvement suggestion, max 8>"],
  "score": <integer 0-100 representing match quality>,
  "cargo_identificado": "<job title extracted from the JD, or 'Nao identificado'>",
  "empresa_identificada": "<company name extracted from the JD, or 'Nao identificado'>"
}}

Rules:
- cv_adaptado must preserve all true facts from the original CV.
- cover_letter must reference specific JD requirements.
- linkedin_message must be under 300 characters, no hashtags, personal and direct.
- keywords lists must contain real skills/tools/technologies.
- score must reflect genuine keyword coverage and experience alignment.
- Return ONLY the JSON object, nothing else.
"""


def adapt_cv(cv_text: str, job_description: str) -> dict:
    """Call Gemini and return the structured result dict."""
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = PROMPT_TEMPLATE.format(
        cv_text=cv_text[:6000],
        job_description=job_description[:4000],
    )

    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            logger.info("Calling Gemini model: %s (attempt %d)", settings.AI_MODEL, attempt + 1)
            response = client.models.generate_content(
                model=settings.AI_MODEL,
                contents=prompt,
            )
            break  # success
        except genai_errors.APIError as exc:
            status_code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
            if status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES - 1:
                wait = _BACKOFF_BASE ** attempt
                logger.warning(
                    "Gemini returned %s on attempt %d — retrying in %ds…",
                    status_code, attempt + 1, wait,
                )
                time.sleep(wait)
                last_exc = exc
            else:
                raise
        except Exception:
            raise
    else:
        raise last_exc  # all retries exhausted

    raw = response.text.strip()

    # Strip any accidental markdown fencing
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    result = json.loads(raw)

    # Ensure all required keys exist with safe defaults
    defaults = {
        "cv_adaptado": "",
        "cover_letter": "",
        "linkedin_message": "",
        "keywords_encontradas": [],
        "keywords_faltando": [],
        "sugestoes": [],
        "score": 0,
        "cargo_identificado": "Nao identificado",
        "empresa_identificada": "Nao identificado",
    }
    for key, default in defaults.items():
        result.setdefault(key, default)

    return result

