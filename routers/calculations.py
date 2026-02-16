"""
Router: /api/v1/calculations
------------------------------
Provides dedicated endpoints for the retirement calculation engine.
Keeps calculation concerns separate from onboarding concerns.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from services.calculation_service import CalculationService
from services.onboarding import OnboardingService
from services.assumption_service import AssumptionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/calculations",
    tags=["calculations"],
)


# ── Run a fresh calculation ───────────────────────────────────────────────────

@router.post("/run/{user_id}", status_code=status.HTTP_201_CREATED)
async def run_calculation(user_id: str):
    """
    Trigger a full retirement calculation for a user.

    Steps performed (all inside this single call):
    1. Load active system assumptions from DB
    2. Call Groq LLM to refine assumptions (if GROQ_API_KEY is set)
    3. Persist any new LLM assumption overrides as a new assumption version
    4. Run the RetirementEngine with merged assumptions
    5. Persist the calculation result to `retirement_calculations`
    6. Persist up to 3 action recommendations to `action_recommendations`
    7. Return the full result including assumption_version_id
    """
    snapshot = OnboardingService.get_user_snapshot(user_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = CalculationService.calculate_and_store(user_id, snapshot)
    except Exception as exc:
        logger.error(f"run_calculation error for user={user_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    return {"success": True, "data": result}


# ── Fetch latest persisted calculation ───────────────────────────────────────

@router.get("/latest/{user_id}")
async def get_latest_calculation(user_id: str):
    """
    Retrieve the most-recent retirement projection that was persisted for this user.

    Returns the calculation result plus its linked active recommendations.
    Returns 404 if the user has never run a calculation.
    """
    try:
        result = CalculationService.get_latest(user_id)
    except Exception as exc:
        logger.error(f"get_latest error for user={user_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No calculation found. Run POST /calculations/run/{user_id} first.",
        )

    return {"success": True, "data": result}


# ── Calculation history ───────────────────────────────────────────────────────

@router.get("/history/{user_id}")
async def get_calculation_history(user_id: str, limit: int = 10):
    """
    Return the last `limit` calculations for a user, newest first.

    Useful for building a "how has your readiness score changed?" timeline
    on the dashboard.
    """
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 50")

    try:
        history = CalculationService.get_history(user_id, limit=limit)
    except Exception as exc:
        logger.error(f"get_history error for user={user_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    return {"success": True, "count": len(history), "data": history}


# ── System assumptions (read) ─────────────────────────────────────────────────

@router.get("/assumptions/active")
async def get_active_assumptions():
    """
    Return the currently-active set of macro-economic assumptions.

    These are the rates the engine uses when GROQ is not available or
    has not produced an override.
    """
    try:
        assumptions = AssumptionService.get_active()
        version_id  = AssumptionService.get_active_version_id()
    except Exception as exc:
        logger.error(f"get_active_assumptions error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "success": True,
        "assumption_version_id": version_id,
        "data": assumptions,
    }
