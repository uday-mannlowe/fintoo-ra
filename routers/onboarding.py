
from fastapi import APIRouter, HTTPException, status
from models.user import (
    EmailCheckRequest, EmailCheckResponse, OnboardingRequest,
    OnboardingResponse, AddAssetsRequest, AddLoansRequest,
    UpdateIncomeRequest, UpdateExpenseRequest,
    AddPostRetirementIncomeRequest, UpdateAssetRequest, UpdateLoanRequest,
    UserSnapshot,
)
from services.onboarding import OnboardingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"],
    responses={404: {"description": "Not found"}}
)

@router.post("/check-email", response_model=EmailCheckResponse)
async def check_email(request: EmailCheckRequest):
    """
    Check if an email address is already registered
    
    - **email**: Email address to check
    """
    try:
        return OnboardingService.check_email_exists(request.email)
    except Exception as e:
        logger.error(f"Error in check_email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check email"
        )

@router.post("/complete", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(request: OnboardingRequest):
    """
    Complete minimal user onboarding (3-minute setup)
    
    Creates:
    - User account
    - Retirement profile
    - Initial income record
    - Initial expense record
    
    All in a single database transaction.
    """
    try:
        return OnboardingService.create_user_onboarding(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in complete_onboarding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding"
        )

@router.get("/status/{user_id}")
async def get_onboarding_status(user_id: str):
    """
    Get onboarding completion status for a user
    
    Returns percentage completion for:
    - Required steps (profile, income, expenses)
    - Optional steps (assets, loans, post-retirement income)
    """
    try:
        status = OnboardingService.get_onboarding_status(user_id)
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"success": True, "data": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_onboarding_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch onboarding status"
        )

@router.get("/snapshot/{user_id}")
async def get_user_snapshot(user_id: str):
    """
    Get complete financial snapshot for a user
    
    Returns:
    - User details
    - Retirement profile
    - Current income and expenses
    - Total retirement savings
    - Total monthly contributions
    - Total monthly EMI
    """
    try:
        snapshot = OnboardingService.get_user_snapshot(user_id)
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"success": True, "data": snapshot}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user snapshot"
        )

@router.post("/assets/{user_id}")
async def add_retirement_assets(user_id: str, request: AddAssetsRequest):
    """
    Add retirement assets for a user
    
    Asset types: EPF, PPF, NPS, Mutual Funds, Stocks, FD, Other
    """
    try:
        result = OnboardingService.add_retirement_assets(user_id, request)
        return result
    except Exception as e:
        logger.error(f"Error in add_retirement_assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add assets"
        )

@router.post("/loans/{user_id}")
async def add_current_loans(user_id: str, request: AddLoansRequest):
    """
    Add current loans for a user
    
    Loan types: Home, Vehicle, Personal, Education, Other
    """
    try:
        result = OnboardingService.add_current_loans(user_id, request)
        return result
    except Exception as e:
        logger.error(f"Error in add_current_loans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add loans"
        )

@router.post("/income/{user_id}")
async def update_income(user_id: str, request: UpdateIncomeRequest):
    """
    Update user income (versioned update)
    
    Creates a new income record while preserving history.
    The old record is marked as not current and given an end date.
    """
    try:
        result = OnboardingService.update_income(user_id, request)
        return result
    except Exception as e:
        logger.error(f"Error in update_income: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update income"
        )


@router.post("/expenses/{user_id}")
async def update_expense(user_id: str, request: UpdateExpenseRequest):
    """
    Update monthly household expense (versioned).

    Closes the current expense record and creates a new one.
    Auto-triggers retirement recalculation.
    """
    try:
        return OnboardingService.update_expense(user_id, request)
    except Exception as e:
        logger.error(f"Error in update_expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update expense"
        )


@router.post("/post-retirement-income/{user_id}")
async def add_post_retirement_income(user_id: str, request: AddPostRetirementIncomeRequest):
    """
    Add expected post-retirement income sources (pension, rental, annuity).

    These improve projection accuracy but are optional.
    Auto-triggers retirement recalculation.
    """
    try:
        return OnboardingService.add_post_retirement_income(user_id, request)
    except Exception as e:
        logger.error(f"Error in add_post_retirement_income: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add post-retirement income"
        )


@router.put("/assets/{user_id}/{asset_id}")
async def update_retirement_asset(user_id: str, asset_id: str, request: UpdateAssetRequest):
    """
    Update an existing retirement asset (versioned).

    Deactivates the old record and inserts a new one — history preserved.
    Auto-triggers retirement recalculation.
    """
    try:
        return OnboardingService.update_retirement_asset(user_id, asset_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_retirement_asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update asset"
        )


@router.put("/loans/{user_id}/{loan_id}")
async def update_loan(user_id: str, loan_id: str, request: UpdateLoanRequest):
    """
    Update an existing loan — outstanding balance and EMI (versioned).

    Deactivates the old record and inserts a new one — history preserved.
    Auto-triggers retirement recalculation.
    """
    try:
        return OnboardingService.update_loan(user_id, loan_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_loan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update loan"
        )
