"""
LAYER 1 – System Assumptions Service
--------------------------------------
Manages versioned macro-economic assumptions in the database.
Every calculation is linked to the assumption version that was active
at the time it ran.  No assumption is ever overwritten — only superseded.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional

from database import db_manager

logger = logging.getLogger(__name__)

# ── hard-coded safety defaults (used if DB is empty or unreachable) ──────────
_DEFAULTS: Dict[str, Any] = {
    "general_inflation_rate":     0.06,
    "healthcare_inflation_rate":  0.08,
    "pre_retirement_return":      0.12,
    "post_retirement_return":     0.07,
    "life_expectancy_years":      85,
    "safety_buffer_years":        5,
    "epf_interest_rate":          0.0815,
    "ppf_interest_rate":          0.071,
    "nps_expected_return":        0.10,
    "equity_expected_return":     0.12,
    "debt_expected_return":       0.07,
}


class AssumptionService:
    """
    Thin wrapper around the system_assumptions table.

    Usage
    -----
    # fetch active assumptions (reads DB once, cached per request)
    assumptions = AssumptionService.get_active()

    # after Groq updates rates, persist and version them
    version_id = AssumptionService.upsert(new_assumptions, source="groq_llm")
    """

    # ── public API ────────────────────────────────────────────────────────────

    @staticmethod
    def get_active() -> Dict[str, Any]:
        """
        Return the currently-active assumption set from the DB.
        Falls back to hard-coded defaults if nothing is found.
        """
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT assumption_id, assumption_type, value,
                           effective_from, created_at
                    FROM   system_assumptions
                    WHERE  is_current = TRUE
                    ORDER  BY assumption_type
                """)
                rows = cur.fetchall()

            if not rows:
                logger.warning("No active assumptions in DB – using hardcoded defaults.")
                return dict(_DEFAULTS)

            assumptions: Dict[str, Any] = {}
            for row in rows:
                key = row["assumption_type"]
                raw = row["value"]
                assumptions[key] = _cast(key, raw)

            return assumptions

        except Exception as exc:
            logger.error(f"AssumptionService.get_active failed: {exc} – using defaults.")
            return dict(_DEFAULTS)

    @staticmethod
    def get_active_version_id() -> Optional[str]:
        """
        Return the assumption_id (UUID str) of the *first* active row.
        Used to link calculations → assumption version.
        """
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT assumption_id::text
                    FROM   system_assumptions
                    WHERE  is_current = TRUE
                    ORDER  BY created_at DESC
                    LIMIT  1
                """)
                row = cur.fetchone()
            return row["assumption_id"] if row else None
        except Exception as exc:
            logger.error(f"get_active_version_id failed: {exc}")
            return None

    @staticmethod
    def upsert(new_values: Dict[str, Any], source: str = "system") -> Optional[str]:
        """
        Persist a new set of assumptions (one row per key).
        Marks old rows for each key as inactive first.

        Returns the last inserted assumption_id as a string, or None on failure.
        """
        if not new_values:
            return None

        try:
            last_id: Optional[str] = None

            with db_manager.get_cursor(commit=True) as cur:
                for key, value in new_values.items():
                    if key == "rationale":  # not a numeric assumption
                        continue

                    # deactivate previous version of this key
                    cur.execute("""
                        UPDATE system_assumptions
                        SET    is_current  = FALSE,
                               effective_to = %s
                        WHERE  assumption_type = %s
                          AND  is_current = TRUE
                    """, (date.today(), key))

                    # insert new active row
                    cur.execute("""
                        INSERT INTO system_assumptions
                               (assumption_type, assumption_name, value,
                                description, effective_from, is_current)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                        RETURNING assumption_id::text
                    """, (
                        key,
                        key,
                        value,
                        new_values.get("rationale", f"source={source}"),
                        date.today(),
                    ))
                    row = cur.fetchone()
                    if row:
                        last_id = row["assumption_id"]

            logger.info(f"AssumptionService: persisted new assumptions from '{source}'")
            return last_id

        except Exception as exc:
            logger.error(f"AssumptionService.upsert failed: {exc}")
            return None

    @staticmethod
    def seed_defaults_if_empty() -> None:
        """
        Called once on app startup.  Inserts the hard-coded defaults only if
        the system_assumptions table is completely empty.
        """
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM system_assumptions")
                if cur.fetchone()["cnt"] > 0:
                    return          # already seeded – nothing to do

            AssumptionService.upsert(_DEFAULTS, source="seed_defaults")
            logger.info("AssumptionService: seeded default assumptions into DB.")

        except Exception as exc:
            logger.warning(f"Could not seed defaults: {exc}")


# ── internal helper ───────────────────────────────────────────────────────────

_INT_KEYS = {"life_expectancy_years", "safety_buffer_years"}

def _cast(key: str, raw: Any) -> Any:
    """Cast a raw DB string to float or int depending on the key."""
    try:
        return int(float(raw)) if key in _INT_KEYS else float(raw)
    except (TypeError, ValueError):
        return raw
