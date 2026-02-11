import math
from typing import Dict, List, Tuple

class RetirementEngine:
    """
    Comprehensive retirement calculation engine
    """
    
    def __init__(self, assumptions: Dict = None):
        self.GENERAL_INFLATION = 0.06
        self.HEALTHCARE_INFLATION = 0.08
        self.PRE_RETIREMENT_RETURN = 0.12
        self.POST_RETIREMENT_RETURN = 0.07
        self.LIFE_EXPECTANCY = 85
        self.SAFETY_BUFFER_YEARS = 5

        self.assumptions_used = self._apply_assumptions(assumptions or {})
    
    def calculate_retirement_projection(self, user_data: Dict) -> Dict:
        """Main calculation function"""
        current_age = self._to_int(user_data.get('current_age'), 0)
        retirement_age = self._to_int(user_data.get('desired_retirement_age'), current_age)
        monthly_expense = self._to_float(user_data.get('monthly_household_expense'), 0.0)
        current_savings = self._to_float(user_data.get('total_retirement_savings'), 0.0)
        monthly_contribution = self._to_float(user_data.get('total_monthly_contribution'), 0.0)
        
        years_to_retirement = retirement_age - current_age
        
        retirement_expense = self._calculate_retirement_expense(
            monthly_expense, years_to_retirement
        )
        
        corpus_required = self._calculate_corpus_required(
            retirement_expense, retirement_age
        )
        
        projected_corpus = self._calculate_projected_corpus(
            current_savings, monthly_contribution, years_to_retirement
        )
        
        gap, readiness_percentage = self._calculate_gap(
            corpus_required, projected_corpus
        )
        
        money_lasts_until = self._calculate_money_lasting_age(
            projected_corpus, retirement_expense, retirement_age
        )
        
        risk_level = self._determine_risk_level(
            readiness_percentage, money_lasts_until
        )
        
        result = {
            'current_age': current_age,
            'retirement_age': retirement_age,
            'current_monthly_expense': monthly_expense,
            'current_monthly_income': self._to_float(user_data.get('monthly_income'), 0.0),
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
            'scenario_id': None,
            'assumptions_used': self.assumptions_used
        }
        
        return result

    def _apply_assumptions(self, assumptions: Dict) -> Dict:
        """Validate and apply dynamic assumptions with safe bounds."""
        if not assumptions:
            return {
                "general_inflation": self.GENERAL_INFLATION,
                "healthcare_inflation": self.HEALTHCARE_INFLATION,
                "pre_retirement_return": self.PRE_RETIREMENT_RETURN,
                "post_retirement_return": self.POST_RETIREMENT_RETURN,
                "life_expectancy": self.LIFE_EXPECTANCY,
                "safety_buffer_years": self.SAFETY_BUFFER_YEARS,
            }

        def _num(value, min_v, max_v, default):
            try:
                v = float(value)
            except Exception:
                return default
            return max(min_v, min(max_v, v))

        def _int(value, min_v, max_v, default):
            try:
                v = int(value)
            except Exception:
                return default
            return max(min_v, min(max_v, v))

        self.GENERAL_INFLATION = _num(
            assumptions.get("general_inflation"),
            0.02, 0.10, self.GENERAL_INFLATION
        )
        self.HEALTHCARE_INFLATION = _num(
            assumptions.get("healthcare_inflation"),
            0.04, 0.12, self.HEALTHCARE_INFLATION
        )
        self.PRE_RETIREMENT_RETURN = _num(
            assumptions.get("pre_retirement_return"),
            0.05, 0.18, self.PRE_RETIREMENT_RETURN
        )
        self.POST_RETIREMENT_RETURN = _num(
            assumptions.get("post_retirement_return"),
            0.03, 0.10, self.POST_RETIREMENT_RETURN
        )
        self.LIFE_EXPECTANCY = _int(
            assumptions.get("life_expectancy"),
            75, 100, self.LIFE_EXPECTANCY
        )
        self.SAFETY_BUFFER_YEARS = _int(
            assumptions.get("safety_buffer_years"),
            0, 10, self.SAFETY_BUFFER_YEARS
        )

        return {
            "general_inflation": self.GENERAL_INFLATION,
            "healthcare_inflation": self.HEALTHCARE_INFLATION,
            "pre_retirement_return": self.PRE_RETIREMENT_RETURN,
            "post_retirement_return": self.POST_RETIREMENT_RETURN,
            "life_expectancy": self.LIFE_EXPECTANCY,
            "safety_buffer_years": self.SAFETY_BUFFER_YEARS,
            "rationale": assumptions.get("rationale", ""),
        }
    
    def _calculate_retirement_expense(self, current_expense: float, years: int) -> float:
        """Calculate monthly expense at retirement"""
        return current_expense * math.pow(1 + self.GENERAL_INFLATION, years)
    
    def _calculate_corpus_required(self, monthly_expense: float, retirement_age: int) -> float:
        """Calculate total corpus needed at retirement"""
        retirement_years = self.LIFE_EXPECTANCY + self.SAFETY_BUFFER_YEARS - retirement_age
        annual_expense = monthly_expense * 12
        
        avg_expense = annual_expense * (1 + (self.HEALTHCARE_INFLATION - self.GENERAL_INFLATION) / 2)
        
        if self.POST_RETIREMENT_RETURN > 0:
            pv_factor = (1 - math.pow(1 + self.POST_RETIREMENT_RETURN, -retirement_years)) / self.POST_RETIREMENT_RETURN
            corpus = avg_expense * pv_factor
        else:
            corpus = avg_expense * retirement_years
        
        return corpus * 1.10
    
    def _calculate_projected_corpus(
        self, current_savings: float, monthly_contribution: float, years: int
    ) -> float:
        """Calculate projected corpus at retirement"""
        fv_current = current_savings * math.pow(1 + self.PRE_RETIREMENT_RETURN, years)
        
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
        max_months = (100 - retirement_age) * 12
        
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
        """Generate actionable recommendations (max 3)"""
        recommendations = []
        gap = calculation_result['corpus_gap']
        readiness = calculation_result['readiness_score']
        years_to_retirement = calculation_result['retirement_age'] - calculation_result['current_age']
        monthly_income = self._to_float(user_data.get('monthly_income'), 0.0)
        total_monthly_emi = self._to_float(user_data.get('total_monthly_emi'), 0.0)
        
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
        
        if total_monthly_emi > monthly_income * 0.4:
            recommendations.append({
                'action_type': 'address_loan',
                'priority': 3,
                'action_title': 'Optimize or prepay high-interest loans',
                'action_description': (
                    f'Your monthly EMI of ₹{int(total_monthly_emi):,} is consuming '
                    f'{(total_monthly_emi / (monthly_income or 1) * 100):.0f}% of your income. '
                    f'Consider prepaying or refinancing to free up cash for retirement savings.'
                ),
                'impact_description': (
                    f'Reducing your EMI burden will improve monthly cash flow and allow you to '
                    f'contribute more towards retirement, potentially increasing readiness by 10-15%.'
                ),
                'suggested_increase_amount': None,
                'suggested_delay_years': None
            })
        
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

    def _to_float(self, value, default=0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    def _to_int(self, value, default=0) -> int:
        try:
            return int(value)
        except Exception:
            return default
