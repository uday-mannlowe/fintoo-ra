from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from config import settings
from database import db_manager

logger = logging.getLogger(__name__)


class AuthService:
    """
    Minimal OTP auth service.
    NOTE: Uses a fixed OTP for now. Replace with real OTP storage later.
    """

    DEBUG_OTP = "1234"

    @staticmethod
    def _get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        try:
            with db_manager.get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT user_id::text, email, full_name
                    FROM users
                    WHERE lower(email) = lower(%s)
                    """,
                    (email,),
                )
                row = cur.fetchone()
            return dict(row) if row else None
        except Exception as exc:
            logger.error(f"_get_user_by_email failed: {exc}")
            return None

    @staticmethod
    def request_otp(email: str) -> Dict[str, Any]:
        user = AuthService._get_user_by_email(email)
        if not user:
            return {
                "success": False,
                "registered": False,
                "message": "Email not registered. Please complete onboarding first.",
            }

        response = {
            "success": True,
            "registered": True,
            "message": "OTP sent successfully.",
            "user_id": user["user_id"],
        }
        if settings.DEBUG:
            response["debug_otp"] = AuthService.DEBUG_OTP
        return response

    @staticmethod
    def verify_otp(email: str, otp: str) -> Dict[str, Any]:
        user = AuthService._get_user_by_email(email)
        if not user:
            return {
                "success": False,
                "message": "User not found. Please complete onboarding first.",
            }

        if str(otp).strip() != AuthService.DEBUG_OTP:
            return {"success": False, "message": "Invalid OTP."}

        return {
            "success": True,
            "message": "OTP verified.",
            "user": user,
        }
