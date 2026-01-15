"""
Enterprise Features Integration
Integrates all enterprise features into the main application.

This module provides a unified interface for all enterprise features
and handles the integration with the Streamlit UI.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import all enterprise modules
from blueprint_generator import BlueprintGenerator, AgentType, generate_agent_blueprint
from refinement_engine import RefinementEngine, RefinementFeedback, refine_with_feedback
from test_generator import TestGenerator, generate_tests_for_prompt
from multi_model_testing import MultiModelTester, AIModel, compare_models
from context_manager import ContextWindowManager, count_tokens, check_fits
from performance_profiler import PerformanceProfiler, CostTracker, start_profiling, stop_profiling
from security_scanner import SecurityScanner, scan_prompt, is_safe
from knowledge_base_manager import KnowledgeBaseManager, create_kb, upload_doc, search_kb
from database import db

logger = logging.getLogger(__name__)


class EnterpriseFeatureManager:
    """Unified manager for all enterprise features."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all feature modules
        self.blueprint_gen = BlueprintGenerator()
        self.refinement_engine = RefinementEngine()
        self.test_generator = TestGenerator()
        self.model_tester = MultiModelTester()
        self.context_manager = ContextWindowManager()
        self.profiler = PerformanceProfiler()
        self.cost_tracker = CostTracker()
        self.security_scanner = SecurityScanner()
        self.kb_manager = KnowledgeBaseManager()
        
        self.logger.info("Enterprise Feature Manager initialized")
    
    def create_agent_blueprint(
        self,
        description: str,
        agent_type: str,
        domain: str,
        use_cases: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a complete agent blueprint.
        
        Returns:
            Dictionary with blueprint and export options
        """
        try:
            self.logger.info(f"Creating {agent_type} agent blueprint")
            
            blueprint = self.blueprint_gen.generate_blueprint(
                agent_description=description,
                agent_type=AgentType(agent_type),
                domain=domain,
                use_cases=use_cases,
                constraints=kwargs.get('constraints'),
                required_integrations=kwargs.get('required_integrations')
            )
            
            return {
                "success": True,
                "blueprint": blueprint,
                "exports": {
                    "json": self.blueprint_gen.export_to_json(blueprint),
                    "python": self.blueprint_gen.export_to_python(blueprint),
                    "markdown": self.blueprint_gen.export_to_markdown(blueprint)
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating blueprint: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def refine_prompt_with_feedback(
        self,
        original_prompt: str,
        current_prompt: str,
        feedback_text: str,
        feedback_type: str = "custom",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Refine a prompt based on user feedback.
        
        Returns:
            Refinement result with improved prompt
        """
        try:
            self.logger.info(f"Refining prompt (iteration {kwargs.get('iteration', 1)})")
            
            feedback = RefinementFeedback(
                iteration=kwargs.get('iteration', 1),
                feedback_type=feedback_type,
                feedback_text=feedback_text,
                specific_issues=kwargs.get('specific_issues', []),
                desired_changes=kwargs.get('desired_changes', [])
            )
            
            from agents import PromptType
            prompt_type = kwargs.get('prompt_type', PromptType.GENERAL)
            
            result = self.refinement_engine.refine_prompt(
                original_prompt=original_prompt,
                current_prompt=current_prompt,
                feedback=feedback,
                prompt_type=prompt_type,
                session_id=kwargs.get('session_id'),
                user_id=kwargs.get('user_id'),
                refinement_history=kwargs.get('refinement_history')
            )
            
            return {
                "success": True,
                "refined_prompt": result.refined_prompt,
                "changes_made": result.changes_made,
                "quality_score": result.quality_score,
                "comparison": result.comparison_to_previous,
                "iteration": result.iteration
            }
        except Exception as e:
            self.logger.error(f"Error refining prompt: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_test_suite(
        self,
        prompt: str,
        prompt_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate comprehensive test suite for a prompt.
        
        Returns:
            Test suite with all test cases
        """
        try:
            self.logger.info(f"Generating test suite for {prompt_type} prompt")
            
            suite = self.test_generator.generate_test_suite(
                prompt=prompt,
                prompt_type=prompt_type,
                agent_capabilities=kwargs.get('agent_capabilities'),
                domain=kwargs.get('domain'),
                constraints=kwargs.get('constraints')
            )
            
            return {
                "success": True,
                "suite": suite,
                "total_tests": suite.total_tests,
                "coverage_areas": suite.coverage_areas,
                "test_cases": [
                    {
                        "name": tc.name,
                        "type": tc.test_type.value,
                        "input": tc.input_data,
                        "expected": tc.expected_output,
                        "criteria": tc.success_criteria,
                        "priority": tc.priority
                    }
                    for tc in suite.test_cases
                ]
            }
        except Exception as e:
            self.logger.error(f"Error generating tests: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def compare_across_models(
        self,
        prompt: str,
        models: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Compare prompt across multiple AI models.
        
        Returns:
            Comparison results with recommendations
        """
        try:
            self.logger.info(f"Comparing across {len(models)} models")
            
            model_enums = [AIModel(m) for m in models]
            
            comparison = self.model_tester.test_prompt_across_models(
                prompt=prompt,
                models=model_enums,
                system_prompt=kwargs.get('system_prompt'),
                temperature=kwargs.get('temperature'),
                max_tokens=kwargs.get('max_tokens')
            )
            
            return {
                "success": True,
                "winner": comparison.winner.value if comparison.winner else None,
                "responses": [
                    {
                        "model": r.model.value,
                        "content": r.content,
                        "latency": r.latency,
                        "tokens": r.tokens_used,
                        "cost": r.cost,
                        "error": r.error
                    }
                    for r in comparison.responses
                ],
                "comparison_matrix": comparison.comparison_matrix,
                "recommendations": comparison.recommendations
            }
        except Exception as e:
            self.logger.error(f"Error comparing models: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_token_usage(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        model: str = "grok-beta"
    ) -> Dict[str, Any]:
        """
        Analyze token usage and provide optimization suggestions.
        
        Returns:
            Token analysis with compression suggestions
        """
        try:
            self.logger.info(f"Analyzing token usage for {model}")
            
            self.context_manager.model = model
            
            token_count = self.context_manager.analyze_context_usage(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context,
                estimated_response_tokens=2000
            )
            
            budget_check = self.context_manager.check_budget(token_count)
            
            suggestions = []
            if not budget_check['within_budget']:
                suggestions = self.context_manager.suggest_compressions(
                    text=context or user_prompt,
                    target_reduction=budget_check['tokens_over_budget'],
                    context_type="general"
                )
            
            return {
                "success": True,
                "token_count": {
                    "total": token_count.total,
                    "system": token_count.system_prompt,
                    "user": token_count.user_prompt,
                    "context": token_count.context,
                    "estimated_response": token_count.estimated_response,
                    "remaining": token_count.remaining,
                    "percentage_used": token_count.percentage_used
                },
                "budget_check": budget_check,
                "compression_suggestions": [
                    {
                        "type": s.type,
                        "description": s.description,
                        "savings": s.savings,
                        "priority": s.priority
                    }
                    for s in suggestions
                ]
            }
        except Exception as e:
            self.logger.error(f"Error analyzing tokens: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def scan_for_security_issues(
        self,
        prompt: str,
        context: Optional[str] = None,
        compliance_standards: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scan prompt for security vulnerabilities.
        
        Returns:
            Security scan results with issues and recommendations
        """
        try:
            self.logger.info("Scanning for security issues")
            
            result = self.security_scanner.scan_prompt(
                prompt=prompt,
                context=context,
                check_compliance=compliance_standards
            )
            
            return {
                "success": True,
                "passed": result.passed,
                "score": result.score,
                "issues": [
                    {
                        "type": issue.type.value,
                        "severity": issue.severity.value,
                        "title": issue.title,
                        "description": issue.description,
                        "location": issue.location,
                        "recommendation": issue.recommendation
                    }
                    for issue in result.issues
                ],
                "warnings": result.warnings,
                "recommendations": result.recommendations,
                "compliance": result.compliance_status
            }
        except Exception as e:
            self.logger.error(f"Error scanning security: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def profile_operation(
        self,
        operation_name: str,
        operation_func: callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Profile an operation and track performance.
        
        Returns:
            Performance metrics and recommendations
        """
        try:
            self.logger.info(f"Profiling operation: {operation_name}")
            
            self.profiler.start_session()
            self.profiler.start_metric(operation_name)
            
            # Execute operation
            result = operation_func(*args, **kwargs)
            
            self.profiler.finish_metric()
            profile_result = self.profiler.end_session()
            
            return {
                "success": True,
                "result": result,
                "performance": {
                    "total_duration": profile_result.total_duration,
                    "total_tokens": profile_result.total_tokens,
                    "total_cost": profile_result.total_cost,
                    "bottlenecks": profile_result.bottlenecks,
                    "recommendations": profile_result.recommendations
                }
            }
        except Exception as e:
            self.logger.error(f"Error profiling operation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_knowledge_base(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new knowledge base for a user.
        
        Returns:
            Knowledge base info
        """
        try:
            self.logger.info(f"Creating knowledge base: {name}")
            
            kb = self.kb_manager.create_knowledge_base(
                user_id=user_id,
                name=name,
                description=description,
                domain=domain
            )
            
            return {
                "success": True,
                "knowledge_base": kb
            }
        except Exception as e:
            self.logger.error(f"Error creating knowledge base: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_knowledge_base(
        self,
        kb_id: int,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search a knowledge base.
        
        Returns:
            Search results
        """
        try:
            self.logger.info(f"Searching knowledge base {kb_id}")
            
            results = self.kb_manager.search(
                kb_id=kb_id,
                query=query,
                top_k=top_k
            )
            
            return {
                "success": True,
                "results": [
                    {
                        "chunk": r.chunk,
                        "document": r.document_name,
                        "score": r.relevance_score,
                        "metadata": r.metadata
                    }
                    for r in results
                ]
            }
        except Exception as e:
            self.logger.error(f"Error searching KB: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_feature_status(self) -> Dict[str, Any]:
        """
        Get status of all enterprise features.
        
        Returns:
            Status dictionary with feature availability
        """
        return {
            "features": {
                "blueprint_generator": {
                    "available": True,
                    "description": "Generate complete agent architectures",
                    "module": "blueprint_generator.py"
                },
                "refinement_engine": {
                    "available": True,
                    "description": "Iterative prompt refinement with feedback",
                    "module": "refinement_engine.py"
                },
                "test_generator": {
                    "available": True,
                    "description": "Auto-generate comprehensive test suites",
                    "module": "test_generator.py"
                },
                "multi_model_testing": {
                    "available": True,
                    "description": "Compare across multiple AI models",
                    "module": "multi_model_testing.py"
                },
                "context_manager": {
                    "available": True,
                    "description": "Token budget and context window management",
                    "module": "context_manager.py"
                },
                "performance_profiler": {
                    "available": True,
                    "description": "Performance tracking and cost analysis",
                    "module": "performance_profiler.py"
                },
                "security_scanner": {
                    "available": True,
                    "description": "Security vulnerability detection",
                    "module": "security_scanner.py"
                },
                "knowledge_base": {
                    "available": True,
                    "description": "Custom domain knowledge management",
                    "module": "knowledge_base_manager.py"
                },
                "collaboration": {
                    "available": True,
                    "description": "Team sharing and comments",
                    "module": "database.py"
                },
                "versioning": {
                    "available": True,
                    "description": "Prompt version control",
                    "module": "database.py"
                }
            },
            "total_features": 10,
            "available_features": 10,
            "status": "All systems operational",
            "timestamp": datetime.now().isoformat()
        }


# Global instance
enterprise_manager = EnterpriseFeatureManager()


# Convenience functions for quick access
def create_blueprint(description: str, agent_type: str, domain: str, use_cases: List[str], **kwargs):
    """Quick blueprint creation."""
    return enterprise_manager.create_agent_blueprint(description, agent_type, domain, use_cases, **kwargs)


def refine_prompt(original: str, current: str, feedback: str, **kwargs):
    """Quick prompt refinement."""
    return enterprise_manager.refine_prompt_with_feedback(original, current, feedback, **kwargs)


def generate_tests(prompt: str, prompt_type: str, **kwargs):
    """Quick test generation."""
    return enterprise_manager.generate_test_suite(prompt, prompt_type, **kwargs)


def compare_models_quick(prompt: str, models: List[str], **kwargs):
    """Quick model comparison."""
    return enterprise_manager.compare_across_models(prompt, models, **kwargs)


def check_security(prompt: str, **kwargs):
    """Quick security check."""
    return enterprise_manager.scan_for_security_issues(prompt, **kwargs)


def analyze_tokens(system_prompt: str, user_prompt: str, **kwargs):
    """Quick token analysis."""
    return enterprise_manager.analyze_token_usage(system_prompt, user_prompt, **kwargs)


def get_status():
    """Get feature status."""
    return enterprise_manager.get_feature_status()
