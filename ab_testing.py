"""
A/B testing module for comparing prompt variants.
"""
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional
from agents import OrchestratorAgent, PromptType
from database import db, ABTest
from input_validation import sanitize_and_validate_prompt, validate_prompt_type

logger = logging.getLogger(__name__)


class ABTesting:
    """Handles A/B testing of prompt variants."""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
    
    def create_test(
        self,
        user_id: Optional[int],
        name: str,
        original_prompt: str,
        variant_a: Optional[str] = None,
        variant_b: Optional[str] = None
    ) -> Optional[ABTest]:
        """
        Create an A/B test.
        
        Args:
            user_id: User ID
            name: Test name
            original_prompt: Original prompt
            variant_a: First variant (optional, will be generated if not provided)
            variant_b: Second variant (optional, will be generated if not provided)
            
        Returns:
            ABTest object
        """
        try:
            # If variants not provided, generate them
            if not variant_a or not variant_b:
                # Generate two optimized variants
                is_valid, sanitized_prompt, _ = sanitize_and_validate_prompt(original_prompt)
                if not is_valid:
                    logger.error("Invalid original prompt")
                    return None
                
                # Use creative type as default for variant generation
                prompt_type = PromptType.CREATIVE
                
                # Generate variant A
                if not variant_a:
                    result_a = self.orchestrator.optimize_prompt(sanitized_prompt, prompt_type)
                    variant_a = result_a.get("optimized_prompt", "")
                
                # Generate variant B with different approach (could use different temperature or prompt)
                if not variant_b:
                    result_b = self.orchestrator.optimize_prompt(sanitized_prompt, prompt_type)
                    variant_b = result_b.get("optimized_prompt", "")
            
            # Create test
            ab_test = db.create_ab_test(user_id, name, original_prompt, variant_a, variant_b)
            return ab_test
        except Exception as e:
            logger.error(f"Error creating A/B test: {str(e)}")
            return None
    
    def get_variant(self, ab_test_id: int) -> str:
        """
        Get a variant for testing (randomly selects A or B).
        
        Args:
            ab_test_id: A/B test ID
            
        Returns:
            Variant prompt ('a' or 'b')
        """
        try:
            db_session = db.get_session()
            ab_test = db_session.query(ABTest).filter(ABTest.id == ab_test_id).first()
            db_session.close()
            
            if not ab_test:
                raise ValueError(f"A/B test {ab_test_id} not found")
            
            # Randomly select variant (50/50 split)
            variant = random.choice(['a', 'b'])
            return variant
        except Exception as e:
            logger.error(f"Error getting variant: {str(e)}")
            return 'a'  # Default to variant A
    
    def record_result(
        self,
        ab_test_id: int,
        variant: str,
        quality_score: float
    ) -> bool:
        """
        Record a test result.
        
        Args:
            ab_test_id: A/B test ID
            variant: Variant tested ('a' or 'b')
            quality_score: Quality score achieved
            
        Returns:
            True if successful
        """
        try:
            db.update_ab_test_results(ab_test_id, variant, quality_score)
            return True
        except Exception as e:
            logger.error(f"Error recording A/B test result: {str(e)}")
            return False
    
    def get_test_results(self, ab_test_id: int) -> Optional[Dict[str, Any]]:
        """
        Get A/B test results and statistics.
        
        Args:
            ab_test_id: A/B test ID
            
        Returns:
            Dictionary with test results
        """
        try:
            db_session = db.get_session()
            ab_test = db_session.query(ABTest).filter(ABTest.id == ab_test_id).first()
            db_session.close()
            
            if not ab_test:
                return None
            
            variant_a_score = ab_test.variant_a_score or 0
            variant_b_score = ab_test.variant_b_score or 0
            variant_a_responses = ab_test.variant_a_responses
            variant_b_responses = ab_test.variant_b_responses
            
            # Calculate winner
            winner = None
            if variant_a_responses > 0 and variant_b_responses > 0:
                if variant_a_score > variant_b_score:
                    winner = 'a'
                elif variant_b_score > variant_a_score:
                    winner = 'b'
                else:
                    winner = 'tie'
            
            return {
                "test_id": ab_test.id,
                "name": ab_test.name,
                "original_prompt": ab_test.original_prompt,
                "variant_a": {
                    "prompt": ab_test.variant_a,
                    "score": variant_a_score,
                    "responses": variant_a_responses
                },
                "variant_b": {
                    "prompt": ab_test.variant_b,
                    "score": variant_b_score,
                    "responses": variant_b_responses
                },
                "winner": winner,
                "status": ab_test.status,
                "created_at": ab_test.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting test results: {str(e)}")
            return None
    
    def complete_test(self, ab_test_id: int) -> bool:
        """
        Mark an A/B test as completed.
        
        Args:
            ab_test_id: A/B test ID
            
        Returns:
            True if successful
        """
        try:
            db_session = db.get_session()
            ab_test = db_session.query(ABTest).filter(ABTest.id == ab_test_id).first()
            if ab_test:
                ab_test.status = "completed"
                ab_test.completed_at = datetime.utcnow()
                db_session.commit()
            db_session.close()
            return True
        except Exception as e:
            logger.error(f"Error completing A/B test: {str(e)}")
            return False
