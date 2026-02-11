from retirement_engine import RetirementEngine
from services.groq_llm import GroqRetirementAdvisor
import logging

logger = logging.getLogger(__name__)

class CalculationService:
    """Service for retirement calculations"""
    
    @staticmethod
    def calculate_and_store(user_id: str, user_data: dict) -> dict:
        """Calculate retirement projections"""
        try:
            advisor = GroqRetirementAdvisor()
            llm_assumptions = advisor.get_assumptions(user_data)

            engine = RetirementEngine(assumptions=llm_assumptions)
            calculation = engine.calculate_retirement_projection(user_data)
            
            recommendations = engine.generate_action_recommendations(calculation, user_data)
            
            logger.info(f"Calculation complete for user {user_id}: {calculation['readiness_score']}% ready")
            
            return {
                'calculation_id': user_id,
                **calculation,
                'recommendations': recommendations,
                'llm_assumptions': llm_assumptions or {}
            }
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            raise
    
    @staticmethod
    def get_latest(user_id: str) -> dict:
        """Get latest calculation for user"""
        try:
            # This would fetch from database
            return None
        except Exception as e:
            logger.error(f"Error fetching calculation: {e}")
            raise
