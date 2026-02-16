"""
routers/chatbot.py
===================
Uses chatbot_interactions table (already in your DB).
interaction_id is used as session_id.

ENDPOINTS
─────────
POST /api/v1/chatbot/message/{user_id}
  Send any message. Returns confirmation question or direct answer.

POST /api/v1/chatbot/confirm/{user_id}/{interaction_id}
  { "confirmed": true }  → apply DB change + recalculate
  { "confirmed": false } → discard, no change

GET  /api/v1/chatbot/history/{user_id}
  Returns full conversation history from chatbot_interactions.

MESSAGES THAT UPDATE THE DB
────────────────────────────
"My salary is now 95000"             → income_update   → income_records
"My expenses increased to 60000"     → expense_update  → expense_records
"I started SIP of 8000/month"        → asset_add       → retirement_assets
"My EPF is now 5 lakhs"              → asset_update    → retirement_assets
"I took a home loan of 40L at 8.5%"  → loan_add        → current_loans
"My home loan EMI reduced to 28000"  → loan_update     → current_loans
"I want to retire at 58"             → retirement_age_update → retirement_profiles
"I'll get 12000 pension from age 60" → post_retirement_income → post_retirement_income
"Am I on track for retirement?"      → general_query   → NO DB change
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chatbot_service import (
    DB_CHANGING_INTENTS,
    extract_intent,
    save_interaction,
    get_pending_interaction,
    confirm_interaction,
    execute_intent,
    answer_general_query,
    get_chat_history,
)
from services.onboarding import OnboardingService
from services.calculation_service import CalculationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


# ── Request / Response models ─────────────────────────────────────────────────

class MessageRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    confirmed: bool


# ── 1. Send a message ─────────────────────────────────────────────────────────

@router.post("/message/{user_id}")
async def send_message(user_id: str, req: MessageRequest):
    """
    Send any chat message.

    Response status values:
      confirmation_required  → Groq found a data change; show Yes/No to user
      clarification_needed   → some fields missing; ask follow-up
      answer                 → general question; answered directly, no DB change
    """
    # Load user's current financial snapshot
    snapshot = OnboardingService.get_user_snapshot(user_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="User not found")

    # ── Extract intent via Groq ───────────────────────────────────────────
    intent_data  = extract_intent(req.message, snapshot)
    intent       = intent_data.get("intent", "general_query")
    confidence   = float(intent_data.get("confidence", 0))
    missing      = intent_data.get("missing_fields", [])
    confirm_msg  = intent_data.get("confirmation_message", "")

    # ── General query or low confidence → answer immediately ─────────────
    if intent == "general_query" or confidence < 0.4:
        latest_calc = None
        try:
            latest_calc = CalculationService.get_latest(user_id)
        except Exception:
            pass

        answer = answer_general_query(
            intent_data.get("entities", {}).get("question", req.message),
            snapshot,
            latest_calc,
        )
        # Save to chatbot_interactions (no pending confirmation needed)
        interaction_id = save_interaction(
            user_id       = user_id,
            intent_data   = intent_data,
            user_message  = req.message,
            assistant_reply = answer,
            was_confirmed = None,   # not applicable for queries
            led_to_update = False,
        )
        return {
            "status":         "answer",
            "interaction_id": interaction_id,
            "intent":         "general_query",
            "message":        answer,
            "db_updated":     False,
        }

    # ── Missing required fields → ask for clarification ──────────────────
    if missing:
        clarification = _build_clarification(intent, missing)
        interaction_id = save_interaction(
            user_id         = user_id,
            intent_data     = intent_data,
            user_message    = req.message,
            assistant_reply = clarification,
            was_confirmed   = None,
            led_to_update   = False,
        )
        return {
            "status":          "clarification_needed",
            "interaction_id":  interaction_id,
            "intent":          intent,
            "missing_fields":  missing,
            "message":         clarification,
            "db_updated":      False,
        }

    # ── DB-changing intent → save as pending, return confirmation ─────────
    if not confirm_msg:
        confirm_msg = f"I noticed a change to your {intent.replace('_', ' ')}. Should I update your retirement plan?"

    interaction_id = save_interaction(
        user_id         = user_id,
        intent_data     = intent_data,
        user_message    = req.message,
        assistant_reply = confirm_msg,
        was_confirmed   = None,   # NULL = waiting for user yes/no
        led_to_update   = False,
    )

    return {
        "status":          "confirmation_required",
        "interaction_id":  interaction_id,
        "intent":          intent,
        "entities":        intent_data.get("entities", {}),
        "message":         confirm_msg,
        "db_updated":      False,
    }


# ── 2. Confirm or cancel a pending change ────────────────────────────────────

@router.post("/confirm/{user_id}/{interaction_id}")
async def confirm_change(user_id: str, interaction_id: str, req: ConfirmRequest):
    """
    Apply (confirmed=true) or discard (confirmed=false) a pending DB change.

    On success returns the updated readiness score and recommendations.
    """
    pending = get_pending_interaction(interaction_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail="Interaction not found or already processed. "
                   "It may have been confirmed/cancelled already."
        )

    # ── User said No ──────────────────────────────────────────────────────
    if not req.confirmed:
        confirm_interaction(
            interaction_id  = interaction_id,
            confirmed       = False,
            assistant_reply = "No problem! Nothing was changed in your retirement plan.",
            led_to_update   = False,
        )
        return {
            "status":     "cancelled",
            "message":    "No changes were made to your retirement plan.",
            "db_updated": False,
        }

    # ── User said Yes → execute ───────────────────────────────────────────
    intent_data = pending["detected_change"]
    result      = execute_intent(user_id, intent_data)
    success     = result.get("success", False)

    if success:
        # Fetch updated calculation
        updated_calc = None
        try:
            updated_calc = CalculationService.get_latest(user_id)
        except Exception:
            pass

        response_msg = _build_success_message(
            intent_data.get("intent"), result, updated_calc
        )
        confirm_interaction(
            interaction_id  = interaction_id,
            confirmed       = True,
            assistant_reply = response_msg,
            led_to_update   = True,
        )
        return {
            "status":                  "completed",
            "message":                 response_msg,
            "db_updated":              True,
            "recalculation_triggered": True,
            "updated_calculation": {
                "readiness_score":       updated_calc.get("readiness_score")       if updated_calc else None,
                "total_corpus_required": updated_calc.get("total_corpus_required") if updated_calc else None,
                "projected_corpus":      updated_calc.get("projected_corpus")      if updated_calc else None,
                "corpus_gap":            updated_calc.get("corpus_gap")            if updated_calc else None,
                "money_lasts_until_age": updated_calc.get("money_lasts_until_age") if updated_calc else None,
                "risk_level":            updated_calc.get("risk_level")            if updated_calc else None,
                "recommendations":       (updated_calc.get("recommendations") or []) if updated_calc else [],
            } if updated_calc else None,
        }
    else:
        err_msg = f"Sorry, I couldn't apply that change. {result.get('message', '')}"
        confirm_interaction(
            interaction_id  = interaction_id,
            confirmed       = True,
            assistant_reply = err_msg,
            led_to_update   = False,
        )
        return {
            "status":     "failed",
            "message":    err_msg,
            "db_updated": False,
        }


# ── 3. Chat history ───────────────────────────────────────────────────────────

@router.get("/history/{user_id}")
async def chat_history(user_id: str, limit: int = 20):
    """
    Return the last `limit` interactions for a user (oldest first).
    Each item shows: user_message, assistant_reply, intent, was_confirmed, led_to_update.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    try:
        history = get_chat_history(user_id, limit=limit)
        return {"success": True, "count": len(history), "messages": history}
    except Exception as exc:
        logger.error(f"chat_history endpoint failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_clarification(intent: str, missing: list) -> str:
    field_labels = {
        "new_monthly_income":      "your new monthly income amount",
        "new_monthly_expense":     "your new monthly expense amount",
        "current_value":           "the current value of the investment",
        "asset_type":              "the type of investment (EPF, PPF, mutual fund, etc.)",
        "asset_name":              "the name of the investment",
        "monthly_contribution":    "your monthly contribution amount",
        "monthly_emi":             "your monthly EMI amount",
        "principal_amount":        "the total loan amount",
        "outstanding_balance":     "the outstanding loan balance",
        "interest_rate":           "the annual interest rate",
        "loan_type":               "the type of loan (home, vehicle, personal, etc.)",
        "new_retirement_age":      "your new desired retirement age",
        "monthly_amount":          "the monthly amount you will receive",
        "start_age":               "the age at which you will start receiving it",
    }
    readable = [field_labels.get(f, f.replace("_", " ")) for f in missing[:2]]
    return f"To update this, could you please tell me {' and '.join(readable)}?"


def _build_success_message(intent: str, result: Dict, calc: Optional[Dict]) -> str:
    labels = {
        "income_update":          "✅ Your income has been updated.",
        "expense_update":         "✅ Your monthly expenses have been updated.",
        "asset_add":              "✅ New investment added to your retirement plan.",
        "asset_update":           "✅ Investment value updated.",
        "loan_add":               "✅ New loan added to your plan.",
        "loan_update":            "✅ Loan details updated.",
        "retirement_age_update":  "✅ Your retirement age has been updated.",
        "post_retirement_income": "✅ Post-retirement income source added.",
    }
    msg = labels.get(intent, "✅ Your retirement plan has been updated.")

    if calc:
        readiness = calc.get("readiness_score", 0)
        msg += f"\n\n📊 Retirement readiness: **{readiness:.0f}%**"
        gap = calc.get("corpus_gap", 0)
        if gap < 0:
            msg += f" | Shortfall: ₹{abs(gap):,.0f}"
        else:
            msg += f" | Surplus: ₹{gap:,.0f}"
        lasts = calc.get("money_lasts_until_age")
        if lasts:
            msg += f" | Money lasts until age {lasts}"

    return msg
