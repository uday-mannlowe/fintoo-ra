"""
services/chatbot_service.py
============================
Uses ONLY the existing chatbot_interactions table:

  chatbot_interactions columns:
    interaction_id    uuid  PK
    user_id           uuid
    interaction_type  varchar   ← intent  (income_update, loan_add, etc.)
    question_asked    text      ← user message
    user_response     text      ← assistant reply
    detected_change   jsonb     ← full intent_data extracted by Groq
    was_confirmed     boolean   ← NULL=pending, TRUE=confirmed, FALSE=cancelled
    led_to_update     boolean   ← TRUE after DB was changed
    created_at        timestamptz

NO new tables required. interaction_id acts as the session_id.

FLOW
────
1. User sends message → extract_intent() → Groq returns structured JSON
2. Save row with was_confirmed=NULL (pending)  → return interaction_id as session_id
3. User confirms → update row was_confirmed=TRUE, led_to_update=TRUE → execute DB changes
4. Auto-recalculation fires inside OnboardingService methods
"""
from __future__ import annotations

import json
import logging
import math
from datetime import date
from typing import Any, Dict, List, Optional

import requests

from config import settings
from database import db_manager

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Groq helper
# ─────────────────────────────────────────────────────────────────────────────

def _call_groq(messages: List[Dict], temperature: float = 0.2, max_tokens: int = 800) -> Optional[str]:
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set – chatbot LLM unavailable.")
        return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_MODEL,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": messages,
            },
            timeout=settings.GROQ_TIMEOUT_S,
        )
        if resp.status_code >= 400:
            logger.warning(f"Groq HTTP {resp.status_code}: {resp.text[:300]}")
            return None
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning(f"Groq call failed: {exc}")
        return None


def _parse_json(text: str) -> Optional[Dict]:
    """Extract first JSON object from any string."""
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            return json.loads(text[s: e + 1])
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 – Intent extraction
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_SYSTEM = """You are a retirement planning assistant that extracts structured intents.
Return ONLY a JSON object — no prose, no markdown fences.

Schema:
{
  "intent": one of [income_update, expense_update, asset_add, asset_update,
                    loan_add, loan_update, retirement_age_update,
                    post_retirement_income, general_query],
  "confidence": number 0-1,
  "entities": {
    "new_monthly_income":       number or null,
    "new_monthly_expense":      number or null,
    "asset_type":               "epf|ppf|nps|mutual_fund|stocks|fd|other" or null,
    "asset_name":               string or null,
    "current_value":            number or null,
    "monthly_contribution":     number or null,
    "asset_name_hint":          string or null,
    "new_current_value":        number or null,
    "new_monthly_contribution": number or null,
    "loan_type":                "home|vehicle|personal|education|other" or null,
    "principal_amount":         number or null,
    "outstanding_balance":      number or null,
    "monthly_emi":              number or null,
    "interest_rate":            number or null,
    "end_date":                 "YYYY-MM-DD" or null,
    "loan_type_hint":           string or null,
    "new_outstanding_balance":  number or null,
    "new_monthly_emi":          number or null,
    "new_retirement_age":       integer or null,
    "income_type":              "pension|rental|annuity|business|other" or null,
    "monthly_amount":           number or null,
    "start_age":                integer or null,
    "is_guaranteed":            boolean or null,
    "question":                 string or null
  },
  "missing_fields": ["field1"],
  "confirmation_message": "Friendly one-sentence e.g. Your income has changed to ₹X. Should I update your retirement plan?"
}

Rules:
- Convert natural language: "1.2 lakh"→120000, "50k"→50000, "95 thousand"→95000, "2 crore"→2000000
- confirmation_message must be warm and specific with exact values
- For general_query set confidence=1.0 and set question entity"""

DB_CHANGING_INTENTS = {
    "income_update", "expense_update",
    "asset_add", "asset_update",
    "loan_add", "loan_update",
    "retirement_age_update", "post_retirement_income",
}


def extract_intent(user_message: str, user_snapshot: Dict) -> Dict:
    """Call Groq to extract structured intent from user message."""
    context = (
        f"User: age {user_snapshot.get('current_age', '?')}, "
        f"income ₹{user_snapshot.get('monthly_income', 0):,.0f}/mo, "
        f"expense ₹{user_snapshot.get('monthly_household_expense', 0):,.0f}/mo, "
        f"retirement age {user_snapshot.get('desired_retirement_age', '?')}"
    )
    content = _call_groq([
        {"role": "system", "content": _INTENT_SYSTEM},
        {"role": "user",   "content": f"{context}\n\nUser message: {user_message}"},
    ], temperature=0.1, max_tokens=700)

    if not content:
        return _fallback_intent(user_message)

    parsed = _parse_json(content)
    if not parsed or "intent" not in parsed:
        return _fallback_intent(user_message)

    return parsed


def _fallback_intent(msg: str) -> Dict:
    return {
        "intent": "general_query",
        "confidence": 0.5,
        "entities": {"question": msg},
        "missing_fields": [],
        "confirmation_message": "Could you rephrase that? I want to make sure I understand correctly.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – chatbot_interactions table CRUD
# (interaction_id is used as session_id in the API)
# ─────────────────────────────────────────────────────────────────────────────

def save_interaction(
    user_id: str,
    intent_data: Dict,
    user_message: str,
    assistant_reply: str,
    was_confirmed: Optional[bool] = None,
    led_to_update: bool = False,
) -> str:
    """
    Insert one row into chatbot_interactions.
    was_confirmed=None means pending (awaiting user yes/no).
    Returns interaction_id as string (used as session_id by the router).
    """
    try:
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO chatbot_interactions
                       (user_id, interaction_type, question_asked,
                        user_response, detected_change,
                        was_confirmed, led_to_update)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING interaction_id::text
            """, (
                user_id,
                intent_data.get("intent", "general_query"),
                user_message,
                assistant_reply,
                json.dumps(intent_data),
                was_confirmed,
                led_to_update,
            ))
            row = cur.fetchone()
            return row["interaction_id"]
    except Exception as exc:
        logger.error(f"save_interaction failed: {exc}")
        return ""


def get_pending_interaction(interaction_id: str) -> Optional[Dict]:
    """
    Fetch a pending interaction (was_confirmed IS NULL).
    Returns dict with detected_change already parsed to dict.
    """
    try:
        with db_manager.get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT interaction_id::text,
                       user_id::text,
                       interaction_type,
                       question_asked,
                       detected_change,
                       was_confirmed,
                       led_to_update
                FROM   chatbot_interactions
                WHERE  interaction_id = %s
                  AND  was_confirmed IS NULL
            """, (interaction_id,))
            row = cur.fetchone()

        if not row:
            return None

        result = dict(row)
        # detected_change can come back as dict (psycopg2 jsonb) or string
        dc = result.get("detected_change")
        if isinstance(dc, str):
            result["detected_change"] = _parse_json(dc) or {}
        return result

    except Exception as exc:
        logger.warning(f"get_pending_interaction failed: {exc}")
        return None


def confirm_interaction(interaction_id: str, confirmed: bool, assistant_reply: str, led_to_update: bool) -> None:
    """Mark interaction as confirmed or cancelled and store final reply."""
    try:
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE chatbot_interactions
                SET    was_confirmed = %s,
                       led_to_update  = %s,
                       user_response  = %s
                WHERE  interaction_id = %s
            """, (confirmed, led_to_update, assistant_reply, interaction_id))
    except Exception as exc:
        logger.warning(f"confirm_interaction failed: {exc}")


def get_chat_history(user_id: str, limit: int = 20) -> List[Dict]:
    """
    Return last `limit` interactions for a user, oldest first.
    Each item has: user_message, assistant_reply, intent, was_confirmed, led_to_update, created_at.
    """
    try:
        with db_manager.get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT
                    interaction_id::text,
                    interaction_type     AS intent,
                    question_asked       AS user_message,
                    user_response        AS assistant_reply,
                    was_confirmed,
                    led_to_update,
                    created_at
                FROM   chatbot_interactions
                WHERE  user_id = %s
                ORDER  BY created_at DESC
                LIMIT  %s
            """, (user_id, limit))
            rows = cur.fetchall()

        history = [dict(r) for r in rows]
        history.reverse()   # oldest → newest for UI display
        return history

    except Exception as exc:
        logger.error(f"get_chat_history failed: {exc}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – Execute confirmed intent → update DB
# ─────────────────────────────────────────────────────────────────────────────

def execute_intent(user_id: str, intent_data: Dict) -> Dict[str, Any]:
    """
    Apply confirmed intent to the database.
    Routes to the correct OnboardingService method.
    Auto-recalculation fires inside each service method via _trigger_recalculation().
    """
    from services.onboarding import OnboardingService
    from models.user import (
        UpdateIncomeRequest, UpdateExpenseRequest,
        RetirementAsset, AssetType, AddAssetsRequest,
        CurrentLoan, LoanType, AddLoansRequest,
        UpdateAssetRequest, UpdateLoanRequest,
        PostRetirementIncomeItem, PostRetirementIncomeType,
        AddPostRetirementIncomeRequest,
    )

    intent   = intent_data.get("intent")
    entities = intent_data.get("entities", {})

    try:
        # ── Income update ─────────────────────────────────────────────────
        if intent == "income_update":
            val = entities.get("new_monthly_income")
            if not val:
                return {"success": False, "message": "Could not extract new income amount."}
            result = OnboardingService.update_income(
                user_id,
                UpdateIncomeRequest(
                    new_monthly_income=float(val),
                    change_reason="Updated via chatbot",
                    updated_by="chatbot",
                ),
            )
            return {**result, "success": True}

        # ── Expense update ────────────────────────────────────────────────
        elif intent == "expense_update":
            val = entities.get("new_monthly_expense")
            if not val:
                return {"success": False, "message": "Could not extract new expense amount."}
            result = OnboardingService.update_expense(
                user_id,
                UpdateExpenseRequest(
                    new_monthly_expense=float(val),
                    change_reason="Updated via chatbot",
                    updated_by="chatbot",
                ),
            )
            return {**result, "success": True}

        # ── Add new asset ─────────────────────────────────────────────────
        elif intent == "asset_add":
            try:
                atype = AssetType((entities.get("asset_type") or "other").lower())
            except ValueError:
                atype = AssetType.other

            asset = RetirementAsset(
                asset_type=atype,
                asset_name=entities.get("asset_name") or atype.value.upper(),
                current_value=float(entities.get("current_value") or 0),
                monthly_contribution=float(entities.get("monthly_contribution") or 0),
            )
            result = OnboardingService.add_retirement_assets(user_id, AddAssetsRequest(assets=[asset]))
            return {**result, "success": True}

        # ── Update existing asset ─────────────────────────────────────────
        elif intent == "asset_update":
            asset_id = _find_asset_id(user_id, entities.get("asset_name_hint", ""))
            if not asset_id:
                return {"success": False, "message": "Could not find that asset. Please add it first via the assets endpoint."}
            result = OnboardingService.update_retirement_asset(
                user_id, asset_id,
                UpdateAssetRequest(
                    current_value=float(entities.get("new_current_value") or 0),
                    monthly_contribution=float(entities.get("new_monthly_contribution") or 0),
                    change_reason="Updated via chatbot",
                ),
            )
            return {**result, "success": True}

        # ── Add new loan ──────────────────────────────────────────────────
        elif intent == "loan_add":
            try:
                ltype = LoanType((entities.get("loan_type") or "other").lower())
            except ValueError:
                ltype = LoanType.other

            principal   = float(entities.get("principal_amount") or entities.get("outstanding_balance") or 0)
            outstanding = float(entities.get("outstanding_balance") or principal)
            emi         = float(entities.get("monthly_emi") or 0)
            rate        = float(entities.get("interest_rate") or 10.0)
            end_dt      = entities.get("end_date") or _estimate_end_date(outstanding, emi, rate)

            loan = CurrentLoan(
                loan_type=ltype,
                principal_amount=principal,
                outstanding_balance=outstanding,
                monthly_emi=emi,
                interest_rate=rate,
                start_date=date.today(),
                end_date=end_dt,
            )
            result = OnboardingService.add_current_loans(user_id, AddLoansRequest(loans=[loan]))
            return {**result, "success": True}

        # ── Update existing loan ──────────────────────────────────────────
        elif intent == "loan_update":
            loan_id = _find_loan_id(user_id, entities.get("loan_type_hint", ""))
            if not loan_id:
                return {"success": False, "message": "Could not find that loan. Please add it first via the loans endpoint."}
            result = OnboardingService.update_loan(
                user_id, loan_id,
                UpdateLoanRequest(
                    outstanding_balance=float(entities.get("new_outstanding_balance") or 0),
                    monthly_emi=float(entities.get("new_monthly_emi") or 0),
                    change_reason="Updated via chatbot",
                ),
            )
            return {**result, "success": True}

        # ── Retirement age ────────────────────────────────────────────────
        elif intent == "retirement_age_update":
            new_age = entities.get("new_retirement_age")
            if not new_age:
                return {"success": False, "message": "Could not extract the new retirement age."}
            return _update_retirement_age(user_id, int(new_age))

        # ── Post-retirement income ────────────────────────────────────────
        elif intent == "post_retirement_income":
            try:
                itype = PostRetirementIncomeType((entities.get("income_type") or "other").lower())
            except ValueError:
                itype = PostRetirementIncomeType.other

            item = PostRetirementIncomeItem(
                income_type=itype,
                monthly_amount=float(entities.get("monthly_amount") or 0),
                start_age=int(entities.get("start_age") or 60),
                is_guaranteed=bool(entities.get("is_guaranteed") or False),
            )
            result = OnboardingService.add_post_retirement_income(
                user_id, AddPostRetirementIncomeRequest(incomes=[item])
            )
            return {**result, "success": True}

        else:
            return {"success": True, "intent": "general_query", "db_updated": False}

    except Exception as exc:
        logger.error(f"execute_intent failed user={user_id} intent={intent}: {exc}")
        return {"success": False, "message": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 – Answer general queries with Groq advice
# ─────────────────────────────────────────────────────────────────────────────

_ADVISOR_SYSTEM = """You are a retirement planning advisor for Indian users.
Answer in simple English, 2-4 sentences. Be direct and actionable.
Use ₹ for amounts. Avoid financial jargon."""


def answer_general_query(question: str, snapshot: Dict, calculation: Optional[Dict]) -> str:
    ctx = [
        f"Age {snapshot.get('current_age')}, retires at {snapshot.get('desired_retirement_age')}",
        f"Income ₹{snapshot.get('monthly_income', 0):,.0f}/mo",
        f"Expense ₹{snapshot.get('monthly_household_expense', 0):,.0f}/mo",
        f"Total savings ₹{snapshot.get('total_retirement_savings', 0):,.0f}",
    ]
    if calculation:
        ctx += [
            f"Readiness {calculation.get('readiness_score', 0):.0f}%",
            f"Corpus required ₹{calculation.get('total_corpus_required', 0):,.0f}",
            f"Gap ₹{calculation.get('corpus_gap', 0):,.0f}",
            f"Money lasts until age {calculation.get('money_lasts_until_age', '?')}",
        ]
    content = _call_groq([
        {"role": "system", "content": _ADVISOR_SYSTEM},
        {"role": "user",   "content": "\n".join(ctx) + f"\n\nQuestion: {question}"},
    ], temperature=0.4, max_tokens=300)
    return content or "I'm here to help with your retirement planning. Could you rephrase your question?"


# ─────────────────────────────────────────────────────────────────────────────
# DB lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

def _find_asset_id(user_id: str, name_hint: str) -> Optional[str]:
    try:
        with db_manager.get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT asset_id::text, asset_name, asset_type
                FROM   retirement_assets
                WHERE  user_id = %s AND is_active = TRUE
                ORDER  BY created_at DESC
            """, (user_id,))
            rows = cur.fetchall()
        if not rows:
            return None
        hint = (name_hint or "").lower()
        for r in rows:
            if hint and (hint in r["asset_name"].lower() or hint in r["asset_type"].lower()):
                return r["asset_id"]
        return rows[0]["asset_id"]   # fallback: most recent
    except Exception as exc:
        logger.warning(f"_find_asset_id: {exc}")
        return None


def _find_loan_id(user_id: str, type_hint: str) -> Optional[str]:
    try:
        with db_manager.get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT loan_id::text, loan_type
                FROM   current_loans
                WHERE  user_id = %s AND is_active = TRUE
                ORDER  BY created_at DESC
            """, (user_id,))
            rows = cur.fetchall()
        if not rows:
            return None
        hint = (type_hint or "").lower()
        for r in rows:
            if hint and hint in r["loan_type"].lower():
                return r["loan_id"]
        return rows[0]["loan_id"]    # fallback: most recent
    except Exception as exc:
        logger.warning(f"_find_loan_id: {exc}")
        return None


def _update_retirement_age(user_id: str, new_age: int) -> Dict:
    try:
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT current_age, marital_status, number_of_dependents
                FROM   retirement_profiles
                WHERE  user_id = %s AND is_current = TRUE
                ORDER  BY created_at DESC LIMIT 1
            """, (user_id,))
            existing = cur.fetchone()
            if not existing:
                return {"success": False, "message": "Retirement profile not found."}
            if new_age <= existing["current_age"]:
                return {"success": False,
                        "message": f"Retirement age must be greater than current age ({existing['current_age']})."}

            # Deactivate current profile
            cur.execute("""
                UPDATE retirement_profiles
                SET    is_current = FALSE
                WHERE  user_id = %s AND is_current = TRUE
            """, (user_id,))

            # Insert new versioned profile
            cur.execute("""
                INSERT INTO retirement_profiles
                       (user_id, current_age, desired_retirement_age,
                        marital_status, number_of_dependents, is_current)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING profile_id::text, desired_retirement_age
            """, (
                user_id,
                existing["current_age"],
                new_age,
                existing["marital_status"],
                existing["number_of_dependents"],
            ))
            row = cur.fetchone()

        # Trigger auto-recalculation
        from services.onboarding import OnboardingService
        OnboardingService._trigger_recalculation(user_id)

        return {
            "success": True,
            "message": f"Retirement age updated to {new_age}",
            "profile": dict(row),
        }
    except Exception as exc:
        logger.error(f"_update_retirement_age failed: {exc}")
        raise


def _estimate_end_date(outstanding: float, emi: float, rate: float) -> str:
    """Estimate loan end date from outstanding balance, EMI, and annual interest rate."""
    try:
        from dateutil.relativedelta import relativedelta
        monthly_rate = rate / 100 / 12
        if emi <= 0 or outstanding <= 0:
            return date.today().replace(year=date.today().year + 5).strftime("%Y-%m-%d")
        if monthly_rate > 0:
            months = -math.log(1 - (outstanding * monthly_rate) / emi) / math.log(1 + monthly_rate)
        else:
            months = outstanding / emi
        end = date.today() + relativedelta(months=int(months) + 1)
        return end.strftime("%Y-%m-%d")
    except Exception:
        return date.today().replace(year=date.today().year + 10).strftime("%Y-%m-%d")
