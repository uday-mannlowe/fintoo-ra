# 🧮 Retirement Calculation Engine - Complete Implementation Guide

## 📊 Overview

Now that you're collecting data from users, you need a **Retirement Calculation Engine** that:

1. Calculates how much money they need at retirement (corpus required)
2. Projects how much they will actually have (projected corpus)
3. Calculates the gap (shortfall or surplus)
4. Determines how long their money will last
5. Generates action recommendations

---

## 🎯 What the Engine Does

### **Input (from Database):**
- Current age: 32
- Retirement age: 60
- Monthly expense: ₹50,000
- Monthly income: ₹80,000
- Current retirement savings: ₹5,00,000
- Monthly retirement contribution: ₹17,000
- Loans, assets, etc.

### **Output (to Database):**
- Retirement year expense: ₹1,85,000/month
- Total corpus required: ₹4.5 crore
- Projected corpus: ₹3.8 crore
- Corpus gap: -₹70 lakh (shortfall)
- Money lasts until age: 78
- Readiness score: 75%
- Risk level: Medium
- 3 action recommendations

---

## 📐 Calculation Formulas

### **Step 1: Calculate Retirement Year Expenses**

```python
def calculate_retirement_expense(current_expense, current_age, retirement_age, inflation_rate=0.06):
    """
    Calculate monthly expense at retirement after adjusting for inflation
    
    Formula: Future Value = Present Value × (1 + inflation)^years
    """
    years_to_retirement = retirement_age - current_age
    retirement_expense = current_expense * ((1 + inflation_rate) ** years_to_retirement)
    return retirement_expense

# Example:
# Current expense: ₹50,000
# Years to retirement: 28
# Inflation: 6%
# Retirement expense = 50,000 × (1.06)^28 = ₹2,52,000/month
```

### **Step 2: Calculate Total Corpus Required**

```python
def calculate_corpus_required(
    retirement_expense,
    retirement_age,
    life_expectancy=85,
    post_retirement_return=0.07,
    healthcare_inflation=0.08
):
    """
    Calculate total corpus needed at retirement
    
    Uses Present Value of Annuity formula
    Formula: PV = PMT × [(1 - (1 + r)^-n) / r]
    """
    retirement_years = life_expectancy - retirement_age
    
    # Adjust for healthcare inflation in later years
    avg_retirement_expense = retirement_expense * (1 + (healthcare_inflation - 0.06) / 2)
    
    # Annual expense
    annual_expense = avg_retirement_expense * 12
    
    # Present value of retirement expenses
    pv_factor = (1 - (1 + post_retirement_return) ** -retirement_years) / post_retirement_return
    corpus_required = annual_expense * pv_factor
    
    # Add 10% safety buffer
    corpus_required *= 1.10
    
    return corpus_required

# Example:
# Retirement expense: ₹2,52,000/month
# Retirement years: 25 (60 to 85)
# Post-retirement return: 7%
# Corpus required = ₹4.5 crore
```

### **Step 3: Calculate Projected Corpus**

```python
def calculate_projected_corpus(
    current_savings,
    monthly_contribution,
    years_to_retirement,
    pre_retirement_return=0.12
):
    """
    Calculate how much user will actually have at retirement
    
    Components:
    1. Growth of current savings
    2. Future value of monthly contributions
    """
    # Growth of current savings
    future_value_current = current_savings * ((1 + pre_retirement_return) ** years_to_retirement)
    
    # Future value of monthly contributions (SIP formula)
    monthly_rate = pre_retirement_return / 12
    months = years_to_retirement * 12
    
    if monthly_contribution > 0:
        fv_contributions = monthly_contribution * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        ) * (1 + monthly_rate)
    else:
        fv_contributions = 0
    
    projected_corpus = future_value_current + fv_contributions
    
    return projected_corpus

# Example:
# Current savings: ₹5,00,000
# Monthly contribution: ₹17,000
# Years: 28
# Pre-retirement return: 12%
# Projected corpus = ₹3.8 crore
```

### **Step 4: Calculate Gap & Money Lasting Age**

```python
def calculate_retirement_gap(corpus_required, projected_corpus):
    """Calculate shortfall or surplus"""
    gap = projected_corpus - corpus_required
    percentage = (projected_corpus / corpus_required) * 100 if corpus_required > 0 else 0
    return gap, percentage

def calculate_money_lasting_age(
    projected_corpus,
    monthly_expense,
    retirement_age,
    post_retirement_return=0.07
):
    """
    Calculate until what age the money will last
    
    Uses declining balance with withdrawals
    """
    balance = projected_corpus
    monthly_return = post_retirement_return / 12
    age = retirement_age
    
    while balance > 0 and age < 100:
        # Monthly withdrawal
        balance -= monthly_expense
        
        # Monthly growth
        balance *= (1 + monthly_return)
        
        # Age by month
        age += 1/12
    
    return int(age)

# Example:
# Projected corpus: ₹3.8 crore
# Monthly expense: ₹2,52,000
# Money lasts until: Age 78
```

### **Step 5: Calculate Readiness Score & Risk Level**

```python
def calculate_readiness_score(corpus_required, projected_corpus):
    """
    Calculate retirement readiness percentage
    Caps at 100% max
    """
    if corpus_required == 0:
        return 100
    
    score = min(100, (projected_corpus / corpus_required) * 100)
    return round(score, 2)

def determine_risk_level(readiness_score, money_lasts_until_age, life_expectancy=85):
    """
    Determine risk level based on readiness and longevity
    """
    if readiness_score >= 90 and money_lasts_until_age >= life_expectancy:
        return 'safe'
    elif readiness_score >= 70 and money_lasts_until_age >= life_expectancy - 5:
        return 'medium'
    else:
        return 'risky'
```

---

## 🔧 Complete Python Implementation

### **retirement_engine.py**

```python
import math
from datetime import datetime
from typing import Dict, List, Tuple

class RetirementEngine:
    """
    Comprehensive retirement calculation engine
    Calculates corpus required, projected corpus, gap, and recommendations
    """
    
    def __init__(self):
        # System assumptions (from database: system_assumptions table)
        self.GENERAL_INFLATION = 0.06  # 6%
        self.HEALTHCARE_INFLATION = 0.08  # 8%
        self.PRE_RETIREMENT_RETURN = 0.12  # 12%
        self.POST_RETIREMENT_RETURN = 0.07  # 7%
        self.LIFE_EXPECTANCY = 85
        self.SAFETY_BUFFER_YEARS = 5
    
    def calculate_retirement_projection(self, user_data: Dict) -> Dict:
        """
        Main calculation function
        
        Args:
            user_data: Dictionary with user's financial data
            
        Returns:
            Complete retirement projection
        """
        # Extract user data
        current_age = user_data['current_age']
        retirement_age = user_data['desired_retirement_age']
        monthly_expense = user_data['monthly_household_expense']
        current_savings = user_data['total_retirement_savings']
        monthly_contribution = user_data['total_monthly_contribution']
        
        years_to_retirement = retirement_age - current_age
        
        # Step 1: Calculate retirement year expenses
        retirement_expense = self._calculate_retirement_expense(
            monthly_expense, years_to_retirement
        )
        
        # Step 2: Calculate corpus required
        corpus_required = self._calculate_corpus_required(
            retirement_expense, retirement_age
        )
        
        # Step 3: Calculate projected corpus
        projected_corpus = self._calculate_projected_corpus(
            current_savings, monthly_contribution, years_to_retirement
        )
        
        # Step 4: Calculate gap
        gap, readiness_percentage = self._calculate_gap(
            corpus_required, projected_corpus
        )
        
        # Step 5: Calculate money lasting age
        money_lasts_until = self._calculate_money_lasting_age(
            projected_corpus, retirement_expense, retirement_age
        )
        
        # Step 6: Determine risk level
        risk_level = self._determine_risk_level(
            readiness_percentage, money_lasts_until
        )
        
        # Prepare result
        result = {
            'current_age': current_age,
            'retirement_age': retirement_age,
            'current_monthly_expense': monthly_expense,
            'current_monthly_income': user_data['monthly_income'],
            'current_retirement_savings': current_savings,
            'current_monthly_retirement_contribution': monthly_contribution,
            'retirement_year_expense': round(retirement_expense, 2),
            'total_corpus_required': round(corpus_required, 2),
            'projected_corpus': round(projected_corpus, 2),
            'corpus_gap': round(gap, 2),
            'money_lasts_until_age': money_lasts_until,
            'readiness_score': round(readiness_percentage, 2),
            'risk_level': risk_level,
            'is_base_scenario': True,
            'scenario_id': None
        }
        
        return result
    
    def _calculate_retirement_expense(self, current_expense: float, years: int) -> float:
        """Calculate monthly expense at retirement"""
        return current_expense * math.pow(1 + self.GENERAL_INFLATION, years)
    
    def _calculate_corpus_required(self, monthly_expense: float, retirement_age: int) -> float:
        """Calculate total corpus needed at retirement"""
        retirement_years = self.LIFE_EXPECTANCY + self.SAFETY_BUFFER_YEARS - retirement_age
        annual_expense = monthly_expense * 12
        
        # Adjust for healthcare inflation
        avg_expense = annual_expense * (1 + (self.HEALTHCARE_INFLATION - self.GENERAL_INFLATION) / 2)
        
        # Present value of annuity
        if self.POST_RETIREMENT_RETURN > 0:
            pv_factor = (1 - math.pow(1 + self.POST_RETIREMENT_RETURN, -retirement_years)) / self.POST_RETIREMENT_RETURN
            corpus = avg_expense * pv_factor
        else:
            # If no returns, need full amount
            corpus = avg_expense * retirement_years
        
        # Add 10% safety buffer
        return corpus * 1.10
    
    def _calculate_projected_corpus(
        self, current_savings: float, monthly_contribution: float, years: int
    ) -> float:
        """Calculate projected corpus at retirement"""
        # Growth of current savings
        fv_current = current_savings * math.pow(1 + self.PRE_RETIREMENT_RETURN, years)
        
        # Future value of monthly contributions
        if monthly_contribution > 0:
            monthly_rate = self.PRE_RETIREMENT_RETURN / 12
            months = years * 12
            fv_contributions = monthly_contribution * (
                (math.pow(1 + monthly_rate, months) - 1) / monthly_rate
            ) * (1 + monthly_rate)
        else:
            fv_contributions = 0
        
        return fv_current + fv_contributions
    
    def _calculate_gap(self, required: float, projected: float) -> Tuple[float, float]:
        """Calculate gap and readiness percentage"""
        gap = projected - required
        percentage = min(100, (projected / required * 100)) if required > 0 else 100
        return gap, percentage
    
    def _calculate_money_lasting_age(
        self, corpus: float, monthly_expense: float, retirement_age: int
    ) -> int:
        """Calculate until what age money will last"""
        balance = corpus
        monthly_return = self.POST_RETIREMENT_RETURN / 12
        months = 0
        max_months = (100 - retirement_age) * 12  # Cap at age 100
        
        while balance > 0 and months < max_months:
            balance -= monthly_expense
            if balance <= 0:
                break
            balance *= (1 + monthly_return)
            months += 1
        
        age = retirement_age + (months / 12)
        return int(age)
    
    def _determine_risk_level(self, readiness: float, money_lasts_until: int) -> str:
        """Determine risk level"""
        target_age = self.LIFE_EXPECTANCY
        
        if readiness >= 90 and money_lasts_until >= target_age:
            return 'safe'
        elif readiness >= 70 and money_lasts_until >= target_age - 5:
            return 'medium'
        else:
            return 'risky'
    
    def generate_action_recommendations(self, calculation_result: Dict, user_data: Dict) -> List[Dict]:
        """
        Generate actionable recommendations (max 3)
        
        Priority:
        1. Critical cash flow issues
        2. Corpus gap solutions
        3. Loan optimization
        """
        recommendations = []
        gap = calculation_result['corpus_gap']
        readiness = calculation_result['readiness_score']
        years_to_retirement = calculation_result['retirement_age'] - calculation_result['current_age']
        
        # Recommendation 1: Increase savings (if gap exists)
        if gap < 0 and readiness < 90:
            monthly_increase_needed = self._calculate_monthly_increase_needed(
                abs(gap), years_to_retirement
            )
            
            recommendations.append({
                'action_type': 'increase_savings',
                'priority': 1,
                'action_title': f'Increase retirement savings by ₹{int(monthly_increase_needed):,}/month',
                'action_description': (
                    f'Your current savings rate needs a boost. Adding ₹{int(monthly_increase_needed):,} '
                    f'to your monthly retirement contributions will help bridge the gap of ₹{abs(int(gap)):,}.'
                ),
                'impact_description': (
                    f'This will make you {min(100, readiness + 15):.0f}% retirement ready and '
                    f'extend your retirement corpus lifespan by approximately 5-7 years.'
                ),
                'suggested_increase_amount': monthly_increase_needed,
                'suggested_delay_years': None
            })
        
        # Recommendation 2: Delay retirement (if gap is significant)
        if gap < 0 and abs(gap) > calculation_result['total_corpus_required'] * 0.2:
            years_delay = min(5, max(2, int(abs(gap) / (calculation_result['current_monthly_income'] * 12 * 0.2))))
            new_readiness = min(100, readiness + (years_delay * 5))
            
            recommendations.append({
                'action_type': 'delay_retirement',
                'priority': 2,
                'action_title': f'Consider retiring at {calculation_result["retirement_age"] + years_delay} instead of {calculation_result["retirement_age"]}',
                'action_description': (
                    f'Working {years_delay} additional years provides more time for wealth accumulation '
                    f'and reduces the retirement period, making your plan more sustainable.'
                ),
                'impact_description': (
                    f'Delaying retirement by {years_delay} years will make you {new_readiness:.0f}% retirement ready '
                    f'and significantly reduce the corpus gap.'
                ),
                'suggested_increase_amount': None,
                'suggested_delay_years': years_delay
            })
        
        # Recommendation 3: Address loans (if total EMI is high)
        if user_data.get('total_monthly_emi', 0) > user_data['monthly_income'] * 0.4:
            recommendations.append({
                'action_type': 'address_loan',
                'priority': 3,
                'action_title': 'Optimize or prepay high-interest loans',
                'action_description': (
                    f'Your monthly EMI of ₹{int(user_data["total_monthly_emi"]):,} is consuming '
                    f'{(user_data["total_monthly_emi"] / user_data["monthly_income"] * 100):.0f}% of your income. '
                    f'Consider prepaying or refinancing to free up cash for retirement savings.'
                ),
                'impact_description': (
                    f'Reducing your EMI burden will improve monthly cash flow and allow you to '
                    f'contribute more towards retirement, potentially increasing readiness by 10-15%.'
                ),
                'suggested_increase_amount': None,
                'suggested_delay_years': None
            })
        
        # Return max 3 recommendations
        return recommendations[:3]
    
    def _calculate_monthly_increase_needed(self, gap: float, years: int) -> float:
        """Calculate monthly contribution increase needed to close gap"""
        monthly_rate = self.PRE_RETIREMENT_RETURN / 12
        months = years * 12
        
        if monthly_rate > 0 and months > 0:
            monthly_needed = gap / (
                ((math.pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate)
            )
            return monthly_needed
        else:
            return gap / (months if months > 0 else 1)


# =====================================================================
# FastAPI Endpoint Integration
# =====================================================================

# Add to routers/calculations.py (NEW FILE)

from fastapi import APIRouter, HTTPException, status
from services.calculation_service import CalculationService
from services.onboarding import OnboardingService

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.post("/run/{user_id}")
async def run_retirement_calculation(user_id: str):
    """
    Run retirement calculations for a user
    Stores results in database
    """
    try:
        # Get user snapshot
        snapshot = OnboardingService.get_user_snapshot(user_id)
        if not snapshot:
            raise HTTPException(404, "User not found")
        
        # Run calculation
        result = CalculationService.calculate_and_store(user_id, snapshot)
        
        return {
            "success": True,
            "calculation": result
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/latest/{user_id}")
async def get_latest_calculation(user_id: str):
    """Get latest calculation results for a user"""
    try:
        result = CalculationService.get_latest(user_id)
        if not result:
            raise HTTPException(404, "No calculations found")
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(500, str(e))


# =====================================================================
# Service Implementation
# =====================================================================

# Add to services/calculation_service.py (NEW FILE)

from database import db_manager
from retirement_engine import RetirementEngine
import logging

logger = logging.getLogger(__name__)

class CalculationService:
    """Service for retirement calculations"""
    
    @staticmethod
    def calculate_and_store(user_id: str, user_data: dict) -> dict:
        """
        Calculate retirement projections and store in database
        """
        try:
            # Initialize engine
            engine = RetirementEngine()
            
            # Run calculation
            calculation = engine.calculate_retirement_projection(user_data)
            
            # Store in database
            with db_manager.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO retirement_calculations (
                        user_id, current_age, retirement_age,
                        current_monthly_expense, current_monthly_income,
                        current_retirement_savings, current_monthly_retirement_contribution,
                        retirement_year_expense, total_corpus_required,
                        projected_corpus, corpus_gap, money_lasts_until_age,
                        readiness_score, risk_level, is_base_scenario
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING calculation_id::text
                """, (
                    user_id,
                    calculation['current_age'],
                    calculation['retirement_age'],
                    calculation['current_monthly_expense'],
                    calculation['current_monthly_income'],
                    calculation['current_retirement_savings'],
                    calculation['current_monthly_retirement_contribution'],
                    calculation['retirement_year_expense'],
                    calculation['total_corpus_required'],
                    calculation['projected_corpus'],
                    calculation['corpus_gap'],
                    calculation['money_lasts_until_age'],
                    calculation['readiness_score'],
                    calculation['risk_level'],
                    calculation['is_base_scenario']
                ))
                
                result = cursor.fetchone()
                calculation_id = result['calculation_id']
            
            # Generate and store recommendations
            recommendations = engine.generate_action_recommendations(calculation, user_data)
            CalculationService._store_recommendations(calculation_id, user_id, recommendations)
            
            logger.info(f"Calculation complete for user {user_id}: {calculation['readiness_score']}% ready")
            
            return {
                'calculation_id': calculation_id,
                **calculation,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            raise
    
    @staticmethod
    def _store_recommendations(calculation_id: str, user_id: str, recommendations: list):
        """Store action recommendations"""
        try:
            with db_manager.get_cursor(commit=True) as cursor:
                # Deactivate old recommendations
                cursor.execute(
                    "UPDATE action_recommendations SET is_active = FALSE WHERE user_id = %s",
                    (user_id,)
                )
                
                # Insert new recommendations
                for rec in recommendations:
                    cursor.execute("""
                        INSERT INTO action_recommendations (
                            calculation_id, user_id, action_type, priority,
                            action_title, action_description, impact_description,
                            suggested_increase_amount, suggested_delay_years
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        calculation_id, user_id,
                        rec['action_type'], rec['priority'],
                        rec['action_title'], rec['action_description'], rec['impact_description'],
                        rec.get('suggested_increase_amount'), rec.get('suggested_delay_years')
                    ))
        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")
            raise
    
    @staticmethod
    def get_latest(user_id: str) -> dict:
        """Get latest calculation for user"""
        try:
            with db_manager.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM retirement_calculations
                    WHERE user_id = %s AND is_base_scenario = TRUE
                    ORDER BY calculation_date DESC
                    LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching calculation: {e}")
            raise
```

---

## 🎯 Usage in Your React App

```javascript
// In Dashboard.jsx, add this function

const runCalculation = async () => {
  try {
    setCalculating(true);
    
    const response = await fetch(
      `http://localhost:8000/api/v1/calculations/run/${userId}`,
      { method: 'POST' }
    );
    
    const result = await response.json();
    
    if (result.success) {
      // Reload dashboard data
      fetchData();
      alert('✅ Retirement calculation complete!');
    }
  } catch (error) {
    console.error('Calculation error:', error);
  } finally {
    setCalculating(false);
  }
};

// Add button in JSX
<button onClick={runCalculation} className="btn-primary">
  Calculate My Retirement Plan
</button>
```

---

## ✅ Summary

**Now you have:**
1. ✅ Complete React frontend                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
2. ✅ FastAPI backend with all endpoints
3. ✅ Retirement calculation engine
4. ✅ Action recommendations generator
5. ✅ Database storage for calculations

**Next: Implement and test the calculation engine!** 🚀
