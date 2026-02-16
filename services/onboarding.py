
from database import db_manager
from models.user import (
    OnboardingRequest, EmailCheckResponse, OnboardingResponse,
    UserResponse, AddAssetsRequest, AddLoansRequest,
    UpdateIncomeRequest, UpdateExpenseRequest,
    AddPostRetirementIncomeRequest, UpdateAssetRequest, UpdateLoanRequest,
)
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OnboardingService:
    """
    Business logic for user onboarding and profile management
    Handles all database operations with proper transaction management
    """
    
    @staticmethod
    def check_email_exists(email: str) -> EmailCheckResponse:
        """Check if email already exists in the database"""
        try:
            with db_manager.get_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM users WHERE email = %s",
                    (email,)
                )
                result = cursor.fetchone()
                exists = result['count'] > 0
                
                return EmailCheckResponse(
                    success=True,
                    exists=exists,
                    can_proceed=not exists,
                    message="Email already registered" if exists else "Email available"
                )
        except Exception as e:
            logger.error(f"Error checking email: {e}")
            raise
    
    @staticmethod
    def create_user_onboarding(data: OnboardingRequest) -> OnboardingResponse:
        """
        Create a new user with minimal onboarding data
        Creates user, profile, income, and expense records in a single transaction
        """
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                # Check if email already exists
                cursor.execute(
                    "SELECT user_id FROM users WHERE email = %s",
                    (data.email,)
                )
                if cursor.fetchone():
                    raise ValueError("Email already registered")
                
                # Create user with all related records in one CTE
                cursor.execute("""
                    WITH new_user AS (
                        INSERT INTO users (email, full_name, phone)
                        VALUES (%s, %s, %s)
                        RETURNING user_id, email, full_name, created_at
                    ),
                    new_profile AS (
                        INSERT INTO retirement_profiles (
                            user_id, current_age, desired_retirement_age, 
                            marital_status, number_of_dependents
                        )
                        SELECT user_id, %s, %s, %s, %s
                        FROM new_user
                        RETURNING user_id
                    ),
                    new_income AS (
                        INSERT INTO income_records (
                            user_id, monthly_income, income_source, 
                            effective_from, is_current
                        )
                        SELECT user_id, %s, 'salary', CURRENT_DATE, TRUE
                        FROM new_user
                        RETURNING user_id
                    ),
                    new_expense AS (
                        INSERT INTO expense_records (
                            user_id, monthly_household_expense, 
                            effective_from, is_current
                        )
                        SELECT user_id, %s, CURRENT_DATE, TRUE
                        FROM new_user
                        RETURNING user_id
                    )
                    SELECT 
                        user_id::text,
                        email,
                        full_name,
                        created_at
                    FROM new_user
                """, (
                    data.email,
                    data.full_name,
                    data.phone,
                    data.current_age,
                    data.desired_retirement_age,
                    data.marital_status.value,
                    data.number_of_dependents,
                    data.monthly_income,
                    data.monthly_expense
                ))
                
                result = cursor.fetchone()
                
                user = UserResponse(
                    user_id=result['user_id'],
                    email=result['email'],
                    full_name=result['full_name'],
                    created_at=result['created_at']
                )
                
                logger.info(f"User created successfully: {user.email}")
                
                return OnboardingResponse(
                    success=True,
                    message="Onboarding completed successfully",
                    user=user
                )
                
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    @staticmethod
    def get_user_snapshot(user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete financial snapshot for a user"""
        try:
            with db_manager.get_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT * FROM vw_current_retirement_snapshot WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                # Convert to dict and handle UUID
                snapshot = dict(result)
                snapshot['user_id'] = str(snapshot['user_id'])
                
                return snapshot
                
        except Exception as e:
            logger.error(f"Error fetching snapshot: {e}")
            raise
    
    @staticmethod
    def add_retirement_assets(user_id: str, data: AddAssetsRequest) -> Dict[str, Any]:
        """Add retirement assets for a user"""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                inserted_assets = []
                
                for asset in data.assets:
                    cursor.execute("""
                        INSERT INTO retirement_assets (
                            user_id, asset_type, asset_name, 
                            current_value, monthly_contribution
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING asset_id::text, asset_type, asset_name, 
                                  current_value, monthly_contribution
                    """, (
                        user_id,
                        asset.asset_type.value,
                        asset.asset_name,
                        asset.current_value,
                        asset.monthly_contribution
                    ))
                    
                    result = cursor.fetchone()
                    inserted_assets.append(dict(result))
                
                logger.info(f"Added {len(inserted_assets)} assets for user {user_id}")
                
                return {
                    "success": True,
                    "message": f"{len(inserted_assets)} asset(s) added successfully",
                    "assets": inserted_assets
                }
                
        except Exception as e:
            logger.error(f"Error adding assets: {e}")
            raise
    
    @staticmethod
    def add_current_loans(user_id: str, data: AddLoansRequest) -> Dict[str, Any]:
        """Add current loans for a user"""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                inserted_loans = []
                
                for loan in data.loans:
                    cursor.execute("""
                        INSERT INTO current_loans (
                            user_id, loan_type, principal_amount, 
                            outstanding_balance, monthly_emi, interest_rate, 
                            start_date, end_date
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING loan_id::text, loan_type, outstanding_balance, monthly_emi
                    """, (
                        user_id,
                        loan.loan_type.value,
                        loan.principal_amount,
                        loan.outstanding_balance,
                        loan.monthly_emi,
                        loan.interest_rate,
                        loan.start_date,
                        loan.end_date
                    ))
                    
                    result = cursor.fetchone()
                    inserted_loans.append(dict(result))
                
                logger.info(f"Added {len(inserted_loans)} loans for user {user_id}")
                
                return {
                    "success": True,
                    "message": f"{len(inserted_loans)} loan(s) added successfully",
                    "loans": inserted_loans
                }
                
        except Exception as e:
            logger.error(f"Error adding loans: {e}")
            raise
    
    @staticmethod
    def update_income(user_id: str, data: UpdateIncomeRequest) -> Dict[str, Any]:
        """Update user income with versioning"""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                # Close current income record
                cursor.execute("""
                    UPDATE income_records 
                    SET effective_to = CURRENT_DATE - INTERVAL '1 day', 
                        is_current = FALSE
                    WHERE user_id = %s AND is_current = TRUE
                """, (user_id,))
                
                # Create new income record
                cursor.execute("""
                    INSERT INTO income_records (
                        user_id, monthly_income, income_source, 
                        effective_from, is_current, updated_by, change_reason
                    )
                    VALUES (%s, %s, 'salary', CURRENT_DATE, TRUE, %s, %s)
                    RETURNING income_id::text, monthly_income, effective_from
                """, (
                    user_id,
                    data.new_monthly_income,
                    data.updated_by,
                    data.change_reason or 'User update'
                ))
                
                result = cursor.fetchone()
                
                logger.info(f"Income updated for user {user_id}")
                
                return {
                    "success": True,
                    "message": "Income updated successfully",
                    "new_income": dict(result)
                }
                
        except Exception as e:
            logger.error(f"Error updating income: {e}")
            raise
    
    @staticmethod
    def get_onboarding_status(user_id: str) -> Dict[str, Any]:
        """Get onboarding completion status for a user"""
        try:
            with db_manager.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        u.user_id::text,
                        u.email,
                        CASE WHEN rp.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_profile,
                        CASE WHEN ir.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_income,
                        CASE WHEN er.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_expenses,
                        CASE WHEN ra.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_assets,
                        CASE WHEN cl.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_loans,
                        CASE WHEN pri.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_post_retirement_income
                    FROM users u
                    LEFT JOIN (SELECT DISTINCT user_id FROM retirement_profiles WHERE is_current = TRUE) rp ON u.user_id = rp.user_id
                    LEFT JOIN (SELECT DISTINCT user_id FROM income_records WHERE is_current = TRUE) ir ON u.user_id = ir.user_id
                    LEFT JOIN (SELECT DISTINCT user_id FROM expense_records WHERE is_current = TRUE) er ON u.user_id = er.user_id
                    LEFT JOIN (SELECT DISTINCT user_id FROM retirement_assets WHERE is_active = TRUE) ra ON u.user_id = ra.user_id
                    LEFT JOIN (SELECT DISTINCT user_id FROM current_loans WHERE is_active = TRUE) cl ON u.user_id = cl.user_id
                    LEFT JOIN (SELECT DISTINCT user_id FROM post_retirement_income WHERE is_active = TRUE) pri ON u.user_id = pri.user_id
                    WHERE u.user_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                status = dict(result)
                
                # Calculate completion percentages
                required_steps = [
                    status['has_profile'],
                    status['has_income'],
                    status['has_expenses']
                ]
                
                optional_steps = [
                    status['has_assets'],
                    status['has_loans'],
                    status['has_post_retirement_income']
                ]
                
                required_completed = sum(required_steps)
                optional_completed = sum(optional_steps)
                
                return {
                    "user_id": status['user_id'],
                    "email": status['email'],
                    "required": {
                        "completed": required_completed,
                        "total": len(required_steps),
                        "percentage": (required_completed / len(required_steps)) * 100,
                        "steps": {
                            "has_profile": status['has_profile'],
                            "has_income": status['has_income'],
                            "has_expenses": status['has_expenses']
                        }
                    },
                    "optional": {
                        "completed": optional_completed,
                        "total": len(optional_steps),
                        "percentage": (optional_completed / len(optional_steps)) * 100,
                        "steps": {
                            "has_assets": status['has_assets'],
                            "has_loans": status['has_loans'],
                            "has_post_retirement_income": status['has_post_retirement_income']
                        }
                    },
                    "overall_percentage": ((required_completed + optional_completed) / (len(required_steps) + len(optional_steps))) * 100
                }
                
        except Exception as e:
            logger.error(f"Error fetching onboarding status: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # NEW METHODS — completing the data collection + versioning layer
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_expense(user_id: str, data: "UpdateExpenseRequest") -> Dict[str, Any]:
        """Versioned expense update — closes old record, inserts new."""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE expense_records
                    SET effective_to = CURRENT_DATE - INTERVAL '1 day',
                        is_current   = FALSE
                    WHERE user_id = %s AND is_current = TRUE
                """, (user_id,))

                cursor.execute("""
                    INSERT INTO expense_records
                           (user_id, monthly_household_expense, effective_from, is_current)
                    VALUES (%s, %s, CURRENT_DATE, TRUE)
                    RETURNING expense_id::text, monthly_household_expense, effective_from
                """, (user_id, data.new_monthly_expense))

                result = cursor.fetchone()
            logger.info(f"Expense updated for user {user_id}")
            OnboardingService._trigger_recalculation(user_id)
            return {"success": True, "message": "Expense updated", "new_expense": dict(result)}
        except Exception as e:
            logger.error(f"Error updating expense: {e}")
            raise

    @staticmethod
    def add_post_retirement_income(user_id: str, data: "AddPostRetirementIncomeRequest") -> Dict[str, Any]:
        """Add one or more post-retirement income sources."""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                inserted = []
                for item in data.incomes:
                    cursor.execute("""
                        INSERT INTO post_retirement_income
                               (user_id, income_type, monthly_amount, start_age, is_guaranteed, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                        RETURNING post_income_id::text AS income_source_id, income_type, monthly_amount, start_age, is_guaranteed
                    """, (
                        user_id,
                        item.income_type.value,
                        item.monthly_amount,
                        item.start_age,
                        item.is_guaranteed,
                    ))
                    inserted.append(dict(cursor.fetchone()))
            logger.info(f"Added {len(inserted)} post-retirement income sources for {user_id}")
            OnboardingService._trigger_recalculation(user_id)
            return {"success": True, "message": f"{len(inserted)} income source(s) added", "incomes": inserted}
        except Exception as e:
            logger.error(f"Error adding post-retirement income: {e}")
            raise

    @staticmethod
    def update_retirement_asset(user_id: str, asset_id: str, data: "UpdateAssetRequest") -> Dict[str, Any]:
        """Versioned asset update — deactivate old record, insert new with updated values."""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                # Fetch existing asset details first
                cursor.execute("""
                    SELECT asset_type, asset_name FROM retirement_assets
                    WHERE asset_id = %s AND user_id = %s AND is_active = TRUE
                """, (asset_id, user_id))
                existing = cursor.fetchone()
                if not existing:
                    raise ValueError(f"Asset {asset_id} not found or not active")

                # Deactivate old
                cursor.execute("""
                    UPDATE retirement_assets SET is_active = FALSE
                    WHERE asset_id = %s AND user_id = %s
                """, (asset_id, user_id))

                # Insert new
                cursor.execute("""
                    INSERT INTO retirement_assets
                           (user_id, asset_type, asset_name, current_value, monthly_contribution, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    RETURNING asset_id::text, asset_type, asset_name, current_value, monthly_contribution
                """, (
                    user_id,
                    existing["asset_type"],
                    existing["asset_name"],
                    data.current_value,
                    data.monthly_contribution,
                ))
                result = cursor.fetchone()
            logger.info(f"Asset updated for user {user_id}, new asset_id={result['asset_id']}")
            OnboardingService._trigger_recalculation(user_id)
            return {"success": True, "message": "Asset updated", "asset": dict(result)}
        except Exception as e:
            logger.error(f"Error updating asset: {e}")
            raise

    @staticmethod
    def update_loan(user_id: str, loan_id: str, data: "UpdateLoanRequest") -> Dict[str, Any]:
        """Versioned loan update — deactivate old record, insert new with updated values."""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    SELECT loan_type, principal_amount, interest_rate, start_date, end_date
                    FROM current_loans
                    WHERE loan_id = %s AND user_id = %s AND is_active = TRUE
                """, (loan_id, user_id))
                existing = cursor.fetchone()
                if not existing:
                    raise ValueError(f"Loan {loan_id} not found or not active")

                cursor.execute("""
                    UPDATE current_loans SET is_active = FALSE
                    WHERE loan_id = %s AND user_id = %s
                """, (loan_id, user_id))

                cursor.execute("""
                    INSERT INTO current_loans
                           (user_id, loan_type, principal_amount, outstanding_balance,
                            monthly_emi, interest_rate, start_date, end_date, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING loan_id::text, loan_type, outstanding_balance, monthly_emi
                """, (
                    user_id,
                    existing["loan_type"],
                    existing["principal_amount"],
                    data.outstanding_balance,
                    data.monthly_emi,
                    existing["interest_rate"],
                    existing["start_date"],
                    existing["end_date"],
                ))
                result = cursor.fetchone()
            logger.info(f"Loan updated for user {user_id}, new loan_id={result['loan_id']}")
            OnboardingService._trigger_recalculation(user_id)
            return {"success": True, "message": "Loan updated", "loan": dict(result)}
        except Exception as e:
            logger.error(f"Error updating loan: {e}")
            raise

    @staticmethod
    def _trigger_recalculation(user_id: str) -> None:
        """
        Auto-trigger retirement recalculation after any data change.
        This is what makes the system 'living' as per the design doc (Section 10).
        Runs synchronously — swap for a background task if needed.
        """
        try:
            from services.calculation_service import CalculationService
            snapshot = OnboardingService.get_user_snapshot(user_id)
            if snapshot:
                CalculationService.calculate_and_store(user_id, snapshot)
                logger.info(f"Auto-recalculation triggered for user {user_id}")
        except Exception as e:
            # Non-fatal — log but don't fail the main operation
            logger.warning(f"Auto-recalculation failed for user {user_id}: {e}")
