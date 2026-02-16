"""
LAYER 3 – Calculation Persistence Service  (full rewrite)
-----------------------------------------------------------
* Persists every retirement calculation result to DB
* Links each result to the assumption version used
* Persists action recommendations (deactivates old ones first)
* get_latest() actually queries the DB
* Exposes history list for timeline views
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import db_manager
from retirement_engine import RetirementEngine
from services.groq_llm import GroqRetirementAdvisor
from services.assumption_service import AssumptionService

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Orchestrates:
      1. Fetch DB assumptions (with Groq override if key present)
      2. Run math engine
      3. Persist calculation row
      4. Persist recommendations (max 3)
      5. Return rich result dict
    """

    # ── main entry point ──────────────────────────────────────────────────────

    @staticmethod
    def calculate_and_store(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full retirement calculation and persist everything to the database.

        Parameters
        ----------
        user_id   : str  – UUID of the user
        user_data : dict – snapshot from vw_current_retirement_snapshot

        Returns
        -------
        dict with calculation results, recommendations, and assumption_version
        """
        try:
            # ── Step 1: Load base assumptions from DB ─────────────────────────
            db_assumptions = AssumptionService.get_active()
            assumption_version_id = AssumptionService.get_active_version_id()

            # ── Step 2: Let Groq refine assumptions (if API key set) ──────────
            advisor = GroqRetirementAdvisor()
            llm_overrides = advisor.get_assumptions(user_data)   # None if not configured

            if llm_overrides:
                # Persist the LLM-suggested assumptions as a new DB version
                new_version = AssumptionService.upsert(llm_overrides, source="groq_llm")
                assumption_version_id = new_version or assumption_version_id
                # Merge: LLM values override DB baseline
                merged_assumptions = {**db_assumptions, **llm_overrides}
            else:
                merged_assumptions = db_assumptions

            # ── Step 3: Run the math engine with merged assumptions ────────────
            engine = RetirementEngine(assumptions=merged_assumptions)
            calculation = engine.calculate_retirement_projection(user_data)

            # ── Step 4: Persist calculation to DB ─────────────────────────────
            calculation_id = CalculationService._persist_calculation(
                user_id, calculation, merged_assumptions, assumption_version_id
            )

            # ── Step 5: Generate and persist recommendations ──────────────────
            recommendations = engine.generate_action_recommendations(calculation, user_data)
            CalculationService._persist_recommendations(
                calculation_id, assumption_version_id, user_id, recommendations
            )

            logger.info(
                f"[Calc] user={user_id}  readiness={calculation['readiness_score']}%  "
                f"calc_id={calculation_id}  assumption_v={assumption_version_id}"
            )

            return {
                "calculation_id": calculation_id,
                "assumption_version_id": assumption_version_id,
                **calculation,
                "recommendations": recommendations,
                "assumptions_used": merged_assumptions,
            }

        except Exception as exc:
            logger.error(f"CalculationService.calculate_and_store failed: {exc}")
            raise

    # ── read endpoints ────────────────────────────────────────────────────────

    @staticmethod
    def get_latest(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Return the most-recent persisted calculation for a user,
        including its active recommendations.
        """
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT
                        c.calculation_id::text,
                        c.assumption_version_id::text,
                        c.user_id::text,
                        c.current_age,
                        c.retirement_age,
                        c.current_monthly_expense,
                        c.current_monthly_income,
                        c.current_retirement_savings,
                        c.current_monthly_retirement_contribution,
                        c.retirement_year_expense,
                        c.total_corpus_required,
                        c.projected_corpus,
                        c.corpus_gap,
                        c.money_lasts_until_age,
                        c.readiness_score,
                        c.risk_level,
                        c.is_base_scenario,
                        c.calculation_date
                    FROM  retirement_calculations c
                    WHERE c.user_id = %s
                      AND c.is_base_scenario = TRUE
                    ORDER BY c.calculation_date DESC
                    LIMIT 1
                """, (user_id,))
                calc_row = cur.fetchone()

            if not calc_row:
                return None

            result = dict(calc_row)

            # Fetch active recommendations for this calculation
            result["recommendations"] = CalculationService._fetch_recommendations(
                user_id, result["calculation_id"]
            )

            return result

        except Exception as exc:
            logger.error(f"get_latest failed for user={user_id}: {exc}")
            raise

    @staticmethod
    def get_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return the last `limit` calculations for a user (newest first).
        Useful for showing progress over time on the dashboard.
        """
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT
                        calculation_id::text,
                        calculation_date,
                        total_corpus_required,
                        projected_corpus,
                        corpus_gap,
                        readiness_score,
                        risk_level,
                        money_lasts_until_age,
                        assumption_version_id::text
                    FROM  retirement_calculations
                    WHERE user_id = %s
                    ORDER BY calculation_date DESC
                    LIMIT %s
                """, (user_id, limit))
                rows = cur.fetchall()

            return [dict(r) for r in rows]

        except Exception as exc:
            logger.error(f"get_history failed for user={user_id}: {exc}")
            raise

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _persist_calculation(
        user_id: str,
        calc: Dict[str, Any],
        assumptions: Dict[str, Any],
        assumption_version_id: Optional[str],
    ) -> str:
        """Insert one row into retirement_calculations, return calculation_id as str."""
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO retirement_calculations (
                    user_id,
                    current_age,
                    retirement_age,
                    current_monthly_expense,
                    current_monthly_income,
                    current_retirement_savings,
                    current_monthly_retirement_contribution,
                    retirement_year_expense,
                    total_corpus_required,
                    projected_corpus,
                    corpus_gap,
                    money_lasts_until_age,
                    readiness_score,
                    risk_level,
                    is_base_scenario,
                    assumption_version_id
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s
                )
                RETURNING calculation_id::text
            """, (
                user_id,
                calc["current_age"],
                calc["retirement_age"],
                calc["current_monthly_expense"],
                calc["current_monthly_income"],
                calc["current_retirement_savings"],
                calc["current_monthly_retirement_contribution"],
                calc["retirement_year_expense"],
                calc["total_corpus_required"],
                calc["projected_corpus"],
                calc["corpus_gap"],
                calc["money_lasts_until_age"],
                calc["readiness_score"],
                calc["risk_level"],
                calc.get("is_base_scenario", True),
                assumption_version_id,
            ))
            row = cur.fetchone()

        return row["calculation_id"]

    @staticmethod
    def _persist_recommendations(
        calculation_id: str,
        assumption_version_id: Optional[str],
        user_id: str,
        recommendations: List[Dict[str, Any]],
    ) -> None:
        """
        Deactivate all previous recommendations for the user,
        then insert the fresh set linked to this calculation.
        """
        with db_manager.get_cursor(commit=True) as cur:
            # Deactivate old ones
            cur.execute("""
                UPDATE action_recommendations
                SET    is_active = FALSE
                WHERE  user_id = %s
            """, (user_id,))

            # Insert fresh recommendations (max 3)
            for rec in recommendations[:3]:
                cur.execute("""
                    INSERT INTO action_recommendations (
                        calculation_id,
                        assumption_version_id,
                        user_id,
                        action_type,
                        priority,
                        action_title,
                        action_description,
                        impact_description,
                        suggested_increase_amount,
                        suggested_delay_years,
                        is_active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """, (
                    calculation_id,
                    assumption_version_id,
                    user_id,
                    rec.get("action_type", "general"),
                    rec.get("priority", 1),
                    rec.get("action_title", ""),
                    rec.get("action_description", ""),
                    rec.get("impact_description", ""),
                    rec.get("suggested_increase_amount"),
                    rec.get("suggested_delay_years"),
                ))

    @staticmethod
    def _fetch_recommendations(user_id: str, calculation_id: str) -> List[Dict[str, Any]]:
        """Return active recommendations for a given calculation."""
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT
                        action_id::text AS recommendation_id,
                        action_type,
                        priority,
                        action_title,
                        action_description,
                        impact_description,
                        suggested_increase_amount,
                        suggested_delay_years
                    FROM  action_recommendations
                    WHERE user_id = %s
                      AND calculation_id = %s
                      AND is_active = TRUE
                    ORDER BY priority ASC
                """, (user_id, calculation_id))
                rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning(f"Could not fetch recommendations: {exc}")
            return []
