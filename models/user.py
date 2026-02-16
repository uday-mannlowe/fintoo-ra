
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class MaritalStatus(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widowed = "widowed"

class EmailCheckRequest(BaseModel):
    email: EmailStr

class EmailCheckResponse(BaseModel):
    success: bool
    exists: bool
    can_proceed: bool
    message: str
    # debug_user_id: Optional[str] = None 

class OnboardingRequest(BaseModel):
    """Request model for minimal onboarding"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    current_age: int = Field(..., ge=18, le=100)
    desired_retirement_age: int = Field(..., ge=18, le=75)
    marital_status: MaritalStatus
    number_of_dependents: int = Field(0, ge=0, le=10)
    monthly_income: float = Field(..., gt=0)
    monthly_expense: float = Field(..., gt=0)
    
    @validator('desired_retirement_age')
    def retirement_age_must_be_greater(cls, v, values):
        if 'current_age' in values and v <= values['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "alice@example.com",
                "full_name": "Alice Smith",
                "phone": "+919876543210",
                "current_age": 32,
                "desired_retirement_age": 60,
                "marital_status": "married",
                "number_of_dependents": 1,
                "monthly_income": 80000,
                "monthly_expense": 50000
            }
        }

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    created_at: datetime

class OnboardingResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse

class AssetType(str, Enum):
    epf = "epf"
    ppf = "ppf"
    nps = "nps"
    mutual_fund = "mutual_fund"
    stocks = "stocks"
    fd = "fd"
    other = "other"

class RetirementAsset(BaseModel):
    asset_type: AssetType
    asset_name: str = Field(..., max_length=255)
    current_value: float = Field(..., ge=0)
    monthly_contribution: float = Field(0, ge=0)

class AddAssetsRequest(BaseModel):
    assets: List[RetirementAsset] = Field(..., min_items=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "assets": [
                    {
                        "asset_type": "epf",
                        "asset_name": "Employee Provident Fund",
                        "current_value": 350000,
                        "monthly_contribution": 12000
                    }
                ]
            }
        }

class LoanType(str, Enum):
    home = "home"
    vehicle = "vehicle"
    personal = "personal"
    education = "education"
    other = "other"

class CurrentLoan(BaseModel):
    loan_type: LoanType
    principal_amount: float = Field(..., gt=0)
    outstanding_balance: float = Field(..., ge=0)
    monthly_emi: float = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0, le=100)
    start_date: date
    end_date: date

    @validator("end_date")
    def end_date_after_start(cls, v, values):
        start = values.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v

class AddLoansRequest(BaseModel):
    loans: List[CurrentLoan] = Field(..., min_items=1)

class UpdateIncomeRequest(BaseModel):
    new_monthly_income: float = Field(..., gt=0)
    change_reason: Optional[str] = None
    updated_by: str = "user"

class UpdateExpenseRequest(BaseModel):
    new_monthly_expense: float = Field(..., gt=0)
    change_reason: Optional[str] = None
    updated_by: str = "user"

class PostRetirementIncomeType(str, Enum):
    pension   = "pension"
    rental    = "rental"
    annuity   = "annuity"
    business  = "business"
    other     = "other"

class PostRetirementIncomeItem(BaseModel):
    income_type:      PostRetirementIncomeType
    monthly_amount:   float = Field(..., gt=0)
    start_age:        int   = Field(..., ge=40, le=100)
    is_guaranteed:    bool  = False

class AddPostRetirementIncomeRequest(BaseModel):
    incomes: List[PostRetirementIncomeItem] = Field(..., min_items=1)

class UpdateAssetRequest(BaseModel):
    current_value:        float = Field(..., ge=0)
    monthly_contribution: float = Field(0, ge=0)
    change_reason:        Optional[str] = None

class UpdateLoanRequest(BaseModel):
    outstanding_balance: float = Field(..., ge=0)
    monthly_emi:         float = Field(..., gt=0)
    change_reason:       Optional[str] = None

class UserSnapshot(BaseModel):
    user_id: str
    email: str
    full_name: str
    current_age: Optional[int]
    desired_retirement_age: Optional[int]
    marital_status: Optional[str]
    number_of_dependents: Optional[int]
    monthly_income: Optional[float]
    monthly_household_expense: Optional[float]
    total_retirement_savings: Optional[float]
    total_monthly_contribution: Optional[float]
    total_monthly_emi: Optional[float]

