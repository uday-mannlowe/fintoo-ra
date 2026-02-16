from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.auth import OtpRequest, OtpVerifyRequest
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp")
async def request_otp(req: OtpRequest):
    """
    Request OTP for an existing user.
    Returns success=false if the email is not registered.
    """
    try:
        return AuthService.request_otp(req.email)
    except Exception as exc:
        logger.error(f"request_otp failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to request OTP")


@router.post("/verify-otp")
async def verify_otp(req: OtpVerifyRequest):
    """
    Verify OTP for an existing user.
    Returns success=false if OTP is invalid.
    """
    try:
        return AuthService.verify_otp(req.email, req.otp)
    except Exception as exc:
        logger.error(f"verify_otp failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")
