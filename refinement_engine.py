"""
Iterative Refinement Engine
Enables feedback-based re-optimization with conversation memory.

Allows users to:
- Provide feedback on optimized prompts
- Iteratively refine based on specific concerns
- Track refinement history
- Compare iterations
- Maintain context across refinements
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from api_utils import generate_completion
from agents import OrchestratorAgent, PromptType
from database import db

logger = logging.getLogger(__name__)


@dataclass
class RefinementFeedback:
    """User feedback for refinement."""
    iteration: int
    feedback_type: str  # "too_vague", "too_specific", "wrong_tone", "missing_context", "custom"
    feedback_text: str
    specific_issues: List[str]
    desired_changes: List[str]


@dataclass
class RefinementResult:
    """Result of a refinement iteration."""
    iteration: int
    refined_prompt: str
    changes_made: str
    quality_score: int
    comparison_to_previous: str
    timestamp: str


class RefinementEngine:
    """Manages iterative prompt refinement with feedback loops."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.orchestrator = OrchestratorAgent()
    
    def refine_prompt(
        self,
        original_prompt: str,
        current_prompt: str,
        feedback: RefinementFeedback,
        prompt_type: PromptType,
        session_id: Optional[int] = None,
        user_id: Optional[int] = None,
        refinement_history: Optional[List[Dict]] = None
    ) -> RefinementResult:
        """
        Refine a prompt based on user feedback.
        
        Args:
            original_prompt: The original user prompt
            current_prompt: The current optimized version
            feedback: User feedback on what to improve
            prompt_type: Type of prompt
            session_id: Optional session ID for tracking
            user_id: Optional user ID
            refinement_history: Optional history of previous refinements
            
        Returns:
            RefinementResult with the refined prompt and metadata
        """
        self.logger.info(f"Starting refinement iteration {feedback.iteration}")
        
        # Build context from history
        context = self._build_context(
            original_prompt,
            current_prompt,
            refinement_history or []
        )
        
        # Generate refinement prompt
        refinement_prompt = self._generate_refinement_prompt(
            original_prompt,
            current_prompt,
            feedback,
            context
        )
        
        # Get refined version
        refined_prompt = self._execute_refinement(
            refinement_prompt,
            prompt_type
        )
        
        # Analyze changes
        changes_made = self._analyze_changes(
            current_prompt,
            refined_prompt,
            feedback
        )
        
        # Evaluate quality
        quality_score = self._evaluate_refinement(
            original_prompt,
            refined_prompt,
            feedback
        )
        
        # Compare to previous
        comparison = self._compare_to_previous(
            current_prompt,
            refined_prompt,
            feedback
        )
        
        # Save to database if session provided
        if session_id and user_id:
            db.add_refinement(
                user_id=user_id,
                session_id=session_id,
                iteration_number=feedback.iteration,
                prompt_text=refined_prompt,
                user_feedback=feedback.feedback_text,
                changes_made=changes_made,
                quality_score=quality_score
            )
        
        return RefinementResult(
            iteration=feedback.iteration,
            refined_prompt=refined_prompt,
            changes_made=changes_made,
            quality_score=quality_score,
            comparison_to_previous=comparison,
            timestamp=datetime.now().isoformat()
        )
    
    def _build_context(
        self,
        original_prompt: str,
        current_prompt: str,
        history: List[Dict]
    ) -> str:
        """Build context from refinement history."""
        if not history:
            return "This is the first refinement iteration."
        
        context_parts = ["Previous refinement iterations:"]
        
        for item in history[-3:]:  # Last 3 iterations
            context_parts.append(f"""
Iteration {item['iteration_number']}:
- Feedback: {item.get('user_feedback', 'N/A')}
- Changes: {item.get('changes_made', 'N/A')}
- Quality Score: {item.get('quality_score', 'N/A')}
""")
        
        return "\n".join(context_parts)
    
    def _generate_refinement_prompt(
        self,
        original_prompt: str,
        current_prompt: str,
        feedback: RefinementFeedback,
        context: str
    ) -> str:
        """Generate the refinement instruction prompt."""
        feedback_type_guidance = {
            "too_vague": "Make the prompt more specific and detailed. Add concrete examples and clear constraints.",
            "too_specific": "Make the prompt more flexible and general. Remove overly restrictive constraints.",
            "wrong_tone": "Adjust the tone and style to better match the user's needs.",
            "missing_context": "Add the missing context and background information.",
            "custom": "Address the specific feedback provided by the user."
        }
        
        guidance = feedback_type_guidance.get(feedback.feedback_type, feedback_type_guidance["custom"])
        
        return f"""You are refining an optimized prompt based on user feedback.

ORIGINAL USER PROMPT:
{original_prompt}

CURRENT OPTIMIZED VERSION:
{current_prompt}

REFINEMENT CONTEXT:
{context}

USER FEEDBACK (Iteration {feedback.iteration}):
Type: {feedback.feedback_type}
Feedback: {feedback.feedback_text}

Specific Issues Identified:
{chr(10).join(f"- {issue}" for issue in feedback.specific_issues)}

Desired Changes:
{chr(10).join(f"- {change}" for change in feedback.desired_changes)}

REFINEMENT GUIDANCE:
{guidance}

Your task:
1. Carefully review the current prompt and user feedback
2. Identify exactly what needs to change
3. Make targeted improvements while preserving what works
4. Ensure the refined prompt addresses all feedback points
5. Maintain clarity, specificity, and actionability

Provide the refined prompt that addresses the feedback while maintaining the quality of the optimization.
Do not include explanations - only output the refined prompt itself."""
    
    def _execute_refinement(
        self,
        refinement_prompt: str,
        prompt_type: PromptType
    ) -> str:
        """Execute the refinement using the orchestrator."""
        try:
            # Use the designer agent directly for refinement
            system_prompt = """You are an expert prompt refinement specialist.
Your job is to take an existing optimized prompt and refine it based on specific feedback.
Make surgical, targeted improvements while preserving what works well.
Output only the refined prompt without explanations or meta-commentary."""
            
            response = generate_completion(
                prompt=refinement_prompt,
                system_prompt=system_prompt,
                temperature=0.5,  # Balanced for refinement
                max_tokens=3000
            )
            
            return response["content"].strip()
        except Exception as e:
            self.logger.error(f"Error executing refinement: {str(e)}")
            raise
    
    def _analyze_changes(
        self,
        previous_prompt: str,
        refined_prompt: str,
        feedback: RefinementFeedback
    ) -> str:
        """Analyze what changed between versions."""
        analysis_prompt = f"""Compare these two prompt versions and describe the key changes made:

PREVIOUS VERSION:
{previous_prompt}

REFINED VERSION:
{refined_prompt}

USER FEEDBACK THAT GUIDED CHANGES:
{feedback.feedback_text}

Provide a concise summary (2-3 sentences) of the main changes made and how they address the feedback."""
        
        try:
            response = generate_completion(
                prompt=analysis_prompt,
                system_prompt="You are a prompt analysis expert. Provide clear, concise change summaries.",
                temperature=0.3,
                max_tokens=500
            )
            return response["content"].strip()
        except Exception as e:
            self.logger.error(f"Error analyzing changes: {str(e)}")
            return "Changes made based on user feedback."
    
    def _evaluate_refinement(
        self,
        original_prompt: str,
        refined_prompt: str,
        feedback: RefinementFeedback
    ) -> int:
        """Evaluate the quality of the refinement (0-100)."""
        evaluation_prompt = f"""Evaluate how well this refined prompt addresses the user's feedback:

ORIGINAL PROMPT:
{original_prompt}

REFINED PROMPT:
{refined_prompt}

USER FEEDBACK:
{feedback.feedback_text}

Specific issues to address:
{chr(10).join(f"- {issue}" for issue in feedback.specific_issues)}

Rate the refinement on a scale of 0-100 based on:
1. How well it addresses the feedback (40 points)
2. Clarity and specificity (20 points)
3. Actionability and completeness (20 points)
4. Improvement over original (20 points)

Respond with ONLY a number between 0 and 100."""
        
        try:
            response = generate_completion(
                prompt=evaluation_prompt,
                system_prompt="You are an objective prompt quality evaluator. Respond with only a number.",
                temperature=0.2,
                max_tokens=10
            )
            
            # Extract number from response
            score_text = response["content"].strip()
            score = int(''.join(filter(str.isdigit, score_text)))
            return min(100, max(0, score))  # Clamp to 0-100
        except Exception as e:
            self.logger.error(f"Error evaluating refinement: {str(e)}")
            return 75  # Default score
    
    def _compare_to_previous(
        self,
        previous_prompt: str,
        refined_prompt: str,
        feedback: RefinementFeedback
    ) -> str:
        """Generate a comparison between versions."""
        comparison_prompt = f"""Provide a brief comparison highlighting improvements:

PREVIOUS:
{previous_prompt[:500]}...

REFINED:
{refined_prompt[:500]}...

FEEDBACK ADDRESSED:
{feedback.feedback_text}

In 2-3 sentences, explain how the refined version improves upon the previous one."""
        
        try:
            response = generate_completion(
                prompt=comparison_prompt,
                system_prompt="You are a concise technical writer. Highlight key improvements.",
                temperature=0.3,
                max_tokens=300
            )
            return response["content"].strip()
        except Exception as e:
            self.logger.error(f"Error generating comparison: {str(e)}")
            return "Refined version addresses user feedback."
    
    def suggest_improvements(
        self,
        prompt: str,
        prompt_type: PromptType,
        context: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        Suggest potential improvements without user feedback.
        Proactive suggestions for further refinement.
        
        Args:
            prompt: The current prompt
            prompt_type: Type of prompt
            context: Optional context about usage/performance
            
        Returns:
            List of improvement suggestions
        """
        suggestion_prompt = f"""Analyze this prompt and suggest 3-5 specific improvements:

PROMPT:
{prompt}

TYPE: {prompt_type.value}

{"CONTEXT: " + str(context) if context else ""}

For each suggestion, provide:
1. Category (clarity, specificity, structure, examples, constraints)
2. Issue: What could be improved
3. Suggestion: Specific improvement to make

Format as JSON array:
[
  {{"category": "...", "issue": "...", "suggestion": "..."}},
  ...
]"""
        
        try:
            response = generate_completion(
                prompt=suggestion_prompt,
                system_prompt="You are a prompt optimization expert. Provide actionable suggestions.",
                temperature=0.4,
                max_tokens=1000
            )
            
            # Parse JSON response
            import json
            suggestions = json.loads(response["content"])
            return suggestions
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {str(e)}")
            return [
                {
                    "category": "general",
                    "issue": "Could be further optimized",
                    "suggestion": "Consider adding more specific examples or constraints"
                }
            ]
    
    def compare_versions(
        self,
        versions: List[Dict[str, Any]],
        highlight_differences: bool = True
    ) -> Dict[str, Any]:
        """
        Compare multiple versions of a prompt.
        
        Args:
            versions: List of version dicts with 'prompt_text', 'version_number', etc.
            highlight_differences: Whether to highlight specific differences
            
        Returns:
            Comparison analysis
        """
        if len(versions) < 2:
            return {"error": "Need at least 2 versions to compare"}
        
        # Sort by version number
        sorted_versions = sorted(versions, key=lambda x: x.get('version_number', 0))
        
        comparison = {
            "total_versions": len(sorted_versions),
            "versions": [],
            "evolution_summary": "",
            "quality_trend": []
        }
        
        # Analyze each version
        for i, version in enumerate(sorted_versions):
            version_info = {
                "version_number": version.get('version_number', i + 1),
                "created_at": version.get('created_at', 'Unknown'),
                "quality_score": version.get('quality_score'),
                "change_description": version.get('change_description', 'N/A'),
                "prompt_length": len(version.get('prompt_text', ''))
            }
            
            if i > 0 and highlight_differences:
                # Compare with previous version
                prev_text = sorted_versions[i-1].get('prompt_text', '')
                curr_text = version.get('prompt_text', '')
                version_info["differences"] = self._highlight_differences(prev_text, curr_text)
            
            comparison["versions"].append(version_info)
            
            if version.get('quality_score'):
                comparison["quality_trend"].append({
                    "version": version.get('version_number', i + 1),
                    "score": version.get('quality_score')
                })
        
        # Generate evolution summary
        comparison["evolution_summary"] = self._generate_evolution_summary(sorted_versions)
        
        return comparison
    
    def _highlight_differences(self, text1: str, text2: str) -> Dict[str, Any]:
        """Highlight differences between two texts."""
        # Simple word-level diff
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        added = words2 - words1
        removed = words1 - words2
        
        return {
            "added_words": len(added),
            "removed_words": len(removed),
            "length_change": len(text2) - len(text1),
            "sample_additions": list(added)[:10] if added else [],
            "sample_removals": list(removed)[:10] if removed else []
        }
    
    def _generate_evolution_summary(self, versions: List[Dict]) -> str:
        """Generate a summary of how the prompt evolved."""
        if len(versions) < 2:
            return "Single version - no evolution to analyze."
        
        first_version = versions[0]
        last_version = versions[-1]
        
        summary_parts = [
            f"Evolved through {len(versions)} iterations.",
            f"Length changed from {len(first_version.get('prompt_text', ''))} to {len(last_version.get('prompt_text', ''))} characters."
        ]
        
        # Quality trend
        scores = [v.get('quality_score') for v in versions if v.get('quality_score')]
        if len(scores) >= 2:
            if scores[-1] > scores[0]:
                summary_parts.append(f"Quality improved from {scores[0]} to {scores[-1]}.")
            elif scores[-1] < scores[0]:
                summary_parts.append(f"Quality decreased from {scores[0]} to {scores[-1]}.")
            else:
                summary_parts.append(f"Quality remained stable at {scores[-1]}.")
        
        return " ".join(summary_parts)
    
    def rollback_to_version(
        self,
        prompt_id: str,
        target_version: int,
        user_id: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Rollback to a previous version.
        
        Args:
            prompt_id: ID of the prompt
            target_version: Version number to rollback to
            user_id: Optional user ID
            
        Returns:
            The rolled-back version data
        """
        try:
            # Get all versions
            versions = db.get_prompt_versions(prompt_id)
            
            # Find target version
            target = next((v for v in versions if v['version_number'] == target_version), None)
            
            if not target:
                self.logger.error(f"Version {target_version} not found")
                return None
            
            # Create new version as rollback
            max_version = max(v['version_number'] for v in versions)
            new_version = db.create_prompt_version(
                user_id=user_id,
                prompt_id=prompt_id,
                version_number=max_version + 1,
                prompt_text=target['prompt_text'],
                prompt_type=target.get('prompt_type'),
                quality_score=target.get('quality_score'),
                change_description=f"Rolled back to version {target_version}",
                parent_version_id=target['id'],
                created_by="system"
            )
            
            if new_version:
                return {
                    "version_number": max_version + 1,
                    "rolled_back_to": target_version,
                    "prompt_text": target['prompt_text'],
                    "message": f"Successfully rolled back to version {target_version}"
                }
            
            return None
        except Exception as e:
            self.logger.error(f"Error rolling back version: {str(e)}")
            return None


# Convenience functions
def refine_with_feedback(
    current_prompt: str,
    feedback_text: str,
    feedback_type: str = "custom",
    specific_issues: Optional[List[str]] = None,
    desired_changes: Optional[List[str]] = None,
    **kwargs
) -> RefinementResult:
    """
    Convenience function for quick refinement.
    
    Args:
        current_prompt: Current prompt to refine
        feedback_text: User's feedback
        feedback_type: Type of feedback
        specific_issues: List of specific issues
        desired_changes: List of desired changes
        **kwargs: Additional arguments (original_prompt, prompt_type, etc.)
        
    Returns:
        RefinementResult
    """
    engine = RefinementEngine()
    
    feedback = RefinementFeedback(
        iteration=kwargs.get('iteration', 1),
        feedback_type=feedback_type,
        feedback_text=feedback_text,
        specific_issues=specific_issues or [],
        desired_changes=desired_changes or []
    )
    
    from agents import PromptType
    prompt_type = kwargs.get('prompt_type', PromptType.GENERAL)
    
    return engine.refine_prompt(
        original_prompt=kwargs.get('original_prompt', current_prompt),
        current_prompt=current_prompt,
        feedback=feedback,
        prompt_type=prompt_type,
        session_id=kwargs.get('session_id'),
        user_id=kwargs.get('user_id'),
        refinement_history=kwargs.get('refinement_history')
    )
