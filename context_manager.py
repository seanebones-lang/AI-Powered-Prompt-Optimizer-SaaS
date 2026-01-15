"""
Context Window Manager
Manages token budgets, context window limits, and prompt compression.

Features:
- Token counting for different models
- Context window simulation
- Budget tracking and alerts
- Automatic compression suggestions
- Token optimization
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ModelContextLimit(Enum):
    """Context window limits for different models."""
    GROK_BETA = 131072  # 128K
    GROK_2 = 131072
    CLAUDE_OPUS = 200000  # 200K
    CLAUDE_SONNET = 200000
    CLAUDE_HAIKU = 200000
    GPT4_TURBO = 128000  # 128K
    GPT4 = 8192  # 8K
    GPT35_TURBO = 16385  # 16K
    GEMINI_PRO = 32768  # 32K
    GEMINI_ULTRA = 1000000  # 1M
    LLAMA_70B = 4096  # 4K


@dataclass
class TokenCount:
    """Token count breakdown."""
    total: int
    system_prompt: int
    user_prompt: int
    context: int
    estimated_response: int
    remaining: int
    percentage_used: float


@dataclass
class CompressionSuggestion:
    """Suggestion for compressing content."""
    type: str  # remove_redundancy, summarize, truncate, abbreviate
    description: str
    original_tokens: int
    compressed_tokens: int
    savings: int
    priority: str  # high, medium, low
    example: Optional[str] = None


class ContextWindowManager:
    """Manages context windows and token budgets."""
    
    def __init__(self, model: str = "grok-beta"):
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.context_limit = self._get_context_limit(model)
    
    def _get_context_limit(self, model: str) -> int:
        """Get context limit for a model."""
        model_key = model.upper().replace("-", "_").replace(".", "_")
        
        try:
            return ModelContextLimit[model_key].value
        except KeyError:
            # Default to 128K if unknown
            self.logger.warning(f"Unknown model {model}, defaulting to 128K context")
            return 131072
    
    def count_tokens(
        self,
        text: str,
        model: Optional[str] = None
    ) -> int:
        """
        Count tokens in text for a specific model.
        
        Note: This is an approximation. For exact counts, use model-specific tokenizers.
        
        Args:
            text: Text to count tokens for
            model: Optional model name (defaults to instance model)
            
        Returns:
            Approximate token count
        """
        if not text:
            return 0
        
        # Simple approximation: ~1.3 tokens per word for English
        # More accurate for GPT models, less so for others
        words = len(text.split())
        chars = len(text)
        
        # Use different heuristics based on model
        target_model = model or self.model
        
        if "gpt" in target_model.lower():
            # GPT tokenizer: ~4 chars per token
            return int(chars / 4)
        elif "claude" in target_model.lower():
            # Claude tokenizer: similar to GPT
            return int(chars / 4)
        elif "grok" in target_model.lower():
            # Grok tokenizer: similar to GPT
            return int(chars / 4)
        else:
            # Default: word-based estimate
            return int(words * 1.3)
    
    def analyze_context_usage(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        estimated_response_tokens: int = 1000
    ) -> TokenCount:
        """
        Analyze context window usage.
        
        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            context: Optional context/history
            estimated_response_tokens: Estimated tokens for response
            
        Returns:
            TokenCount with detailed breakdown
        """
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_prompt)
        context_tokens = self.count_tokens(context) if context else 0
        
        total_input = system_tokens + user_tokens + context_tokens
        total_with_response = total_input + estimated_response_tokens
        
        remaining = self.context_limit - total_with_response
        percentage = (total_with_response / self.context_limit) * 100
        
        return TokenCount(
            total=total_with_response,
            system_prompt=system_tokens,
            user_prompt=user_tokens,
            context=context_tokens,
            estimated_response=estimated_response_tokens,
            remaining=remaining,
            percentage_used=percentage
        )
    
    def check_budget(
        self,
        token_count: TokenCount,
        budget_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if token usage is within budget.
        
        Args:
            token_count: TokenCount object
            budget_limit: Optional custom budget limit
            
        Returns:
            Budget check results with warnings
        """
        limit = budget_limit or self.context_limit
        
        status = "ok"
        warnings = []
        
        if token_count.total > limit:
            status = "exceeded"
            warnings.append(f"Token limit exceeded by {token_count.total - limit} tokens")
        elif token_count.percentage_used > 90:
            status = "critical"
            warnings.append(f"Using {token_count.percentage_used:.1f}% of context window")
        elif token_count.percentage_used > 75:
            status = "warning"
            warnings.append(f"Using {token_count.percentage_used:.1f}% of context window")
        
        if token_count.remaining < 500:
            warnings.append("Very little room for response (< 500 tokens)")
        
        return {
            "status": status,
            "within_budget": token_count.total <= limit,
            "warnings": warnings,
            "usage_percentage": token_count.percentage_used,
            "tokens_over_budget": max(0, token_count.total - limit)
        }
    
    def suggest_compressions(
        self,
        text: str,
        target_reduction: int,
        context_type: str = "general"
    ) -> List[CompressionSuggestion]:
        """
        Suggest ways to compress text to fit within budget.
        
        Args:
            text: Text to compress
            target_reduction: Target token reduction
            context_type: Type of content (general, code, conversation, etc.)
            
        Returns:
            List of compression suggestions
        """
        suggestions = []
        current_tokens = self.count_tokens(text)
        
        # Suggestion 1: Remove redundancy
        redundancy_savings = self._estimate_redundancy_savings(text)
        if redundancy_savings > 0:
            suggestions.append(CompressionSuggestion(
                type="remove_redundancy",
                description="Remove redundant phrases and repetitive content",
                original_tokens=current_tokens,
                compressed_tokens=current_tokens - redundancy_savings,
                savings=redundancy_savings,
                priority="high" if redundancy_savings >= target_reduction * 0.5 else "medium",
                example=self._find_redundancy_example(text)
            ))
        
        # Suggestion 2: Summarize verbose sections
        if len(text) > 1000:
            summary_savings = int(current_tokens * 0.4)  # 40% reduction
            suggestions.append(CompressionSuggestion(
                type="summarize",
                description="Summarize verbose sections while preserving key information",
                original_tokens=current_tokens,
                compressed_tokens=current_tokens - summary_savings,
                savings=summary_savings,
                priority="high" if summary_savings >= target_reduction else "medium"
            ))
        
        # Suggestion 3: Use abbreviations
        abbrev_savings = self._estimate_abbreviation_savings(text)
        if abbrev_savings > 0:
            suggestions.append(CompressionSuggestion(
                type="abbreviate",
                description="Use common abbreviations and shorter forms",
                original_tokens=current_tokens,
                compressed_tokens=current_tokens - abbrev_savings,
                savings=abbrev_savings,
                priority="low",
                example="'for example' → 'e.g.', 'that is' → 'i.e.'"
            ))
        
        # Suggestion 4: Truncate less important sections
        if context_type == "conversation":
            truncate_savings = int(current_tokens * 0.3)
            suggestions.append(CompressionSuggestion(
                type="truncate",
                description="Keep only recent conversation history",
                original_tokens=current_tokens,
                compressed_tokens=current_tokens - truncate_savings,
                savings=truncate_savings,
                priority="medium"
            ))
        
        # Suggestion 5: Remove examples
        example_savings = self._estimate_example_savings(text)
        if example_savings > 0:
            suggestions.append(CompressionSuggestion(
                type="remove_examples",
                description="Remove or shorten examples while keeping instructions",
                original_tokens=current_tokens,
                compressed_tokens=current_tokens - example_savings,
                savings=example_savings,
                priority="medium"
            ))
        
        # Sort by priority and savings
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: (priority_order[x.priority], -x.savings))
        
        return suggestions
    
    def _estimate_redundancy_savings(self, text: str) -> int:
        """Estimate token savings from removing redundancy."""
        # Look for repeated phrases
        words = text.split()
        
        # Count repeated 3-word phrases
        phrases = {}
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            phrases[phrase] = phrases.get(phrase, 0) + 1
        
        # Calculate savings from duplicates
        redundant_tokens = 0
        for phrase, count in phrases.items():
            if count > 1:
                # Each duplicate costs ~3 tokens
                redundant_tokens += (count - 1) * 3
        
        return min(redundant_tokens, int(self.count_tokens(text) * 0.2))  # Max 20% savings
    
    def _find_redundancy_example(self, text: str) -> Optional[str]:
        """Find an example of redundancy in text."""
        words = text.split()
        
        # Look for repeated phrases
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            # Check if phrase appears again
            remaining = " ".join(words[i+3:])
            if phrase in remaining:
                return f"Repeated: '{phrase}'"
        
        return None
    
    def _estimate_abbreviation_savings(self, text: str) -> int:
        """Estimate savings from using abbreviations."""
        abbreviations = {
            "for example": "e.g.",
            "that is": "i.e.",
            "and so on": "etc.",
            "versus": "vs.",
            "approximately": "approx.",
            "maximum": "max",
            "minimum": "min",
            "number": "no.",
            "percent": "%"
        }
        
        savings = 0
        text_lower = text.lower()
        
        for full, abbrev in abbreviations.items():
            count = text_lower.count(full)
            if count > 0:
                # Each replacement saves tokens
                full_tokens = self.count_tokens(full)
                abbrev_tokens = self.count_tokens(abbrev)
                savings += count * (full_tokens - abbrev_tokens)
        
        return savings
    
    def _estimate_example_savings(self, text: str) -> int:
        """Estimate savings from removing examples."""
        # Look for example markers
        example_markers = ["for example", "e.g.", "such as", "like:", "example:"]
        
        example_sections = 0
        for marker in example_markers:
            example_sections += text.lower().count(marker)
        
        if example_sections > 0:
            # Assume each example is ~50 tokens
            return min(example_sections * 50, int(self.count_tokens(text) * 0.3))
        
        return 0
    
    def compress_text(
        self,
        text: str,
        target_tokens: int,
        strategy: str = "auto"
    ) -> Tuple[str, int, List[str]]:
        """
        Automatically compress text to target token count.
        
        Args:
            text: Text to compress
            target_tokens: Target token count
            strategy: Compression strategy (auto, aggressive, conservative)
            
        Returns:
            Tuple of (compressed_text, final_tokens, changes_made)
        """
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= target_tokens:
            return text, current_tokens, []
        
        changes_made = []
        compressed = text
        
        # Strategy 1: Remove redundant whitespace
        compressed = re.sub(r'\s+', ' ', compressed)
        compressed = compressed.strip()
        changes_made.append("Removed extra whitespace")
        
        # Strategy 2: Use abbreviations
        abbreviations = {
            " for example ": " e.g. ",
            " that is ": " i.e. ",
            " and so on": " etc.",
            " approximately ": " ~",
        }
        
        for full, abbrev in abbreviations.items():
            if full in compressed:
                compressed = compressed.replace(full, abbrev)
                changes_made.append(f"Abbreviated '{full.strip()}' to '{abbrev.strip()}'")
        
        # Strategy 3: Remove filler words if aggressive
        if strategy == "aggressive":
            filler_words = [" really ", " very ", " quite ", " just ", " actually "]
            for filler in filler_words:
                if filler in compressed:
                    compressed = compressed.replace(filler, " ")
                    changes_made.append(f"Removed filler word '{filler.strip()}'")
        
        # Strategy 4: Truncate if still over budget
        final_tokens = self.count_tokens(compressed)
        if final_tokens > target_tokens:
            # Calculate how much to keep
            keep_ratio = target_tokens / final_tokens
            keep_chars = int(len(compressed) * keep_ratio)
            
            # Try to truncate at sentence boundary
            truncated = compressed[:keep_chars]
            last_period = truncated.rfind('.')
            if last_period > keep_chars * 0.8:  # If we can keep 80%+
                compressed = truncated[:last_period + 1]
            else:
                compressed = truncated + "..."
            
            changes_made.append(f"Truncated to fit budget")
            final_tokens = self.count_tokens(compressed)
        
        return compressed, final_tokens, changes_made
    
    def optimize_for_model(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        target_model: Optional[str] = None,
        max_response_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Optimize prompts for a specific model's context window.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            context: Optional context
            target_model: Target model (defaults to instance model)
            max_response_tokens: Maximum tokens for response
            
        Returns:
            Optimization results with compressed versions if needed
        """
        model = target_model or self.model
        limit = self._get_context_limit(model)
        
        # Analyze current usage
        token_count = self.analyze_context_usage(
            system_prompt,
            user_prompt,
            context,
            max_response_tokens
        )
        
        # Check budget
        budget_check = self.check_budget(token_count, limit)
        
        result = {
            "model": model,
            "context_limit": limit,
            "token_count": token_count,
            "budget_check": budget_check,
            "optimized": False,
            "original": {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "context": context
            },
            "compressed": {}
        }
        
        # If over budget, compress
        if not budget_check["within_budget"]:
            tokens_to_save = budget_check["tokens_over_budget"] + 500  # Extra buffer
            
            # Try compressing each component
            if token_count.context > 0 and context:
                target_context_tokens = max(100, token_count.context - tokens_to_save)
                compressed_context, final_tokens, changes = self.compress_text(
                    context,
                    target_context_tokens,
                    strategy="aggressive"
                )
                result["compressed"]["context"] = compressed_context
                result["compressed"]["context_changes"] = changes
                tokens_to_save -= (token_count.context - final_tokens)
            
            # If still need to save, compress system prompt
            if tokens_to_save > 0:
                target_system_tokens = max(200, token_count.system_prompt - tokens_to_save)
                compressed_system, final_tokens, changes = self.compress_text(
                    system_prompt,
                    target_system_tokens,
                    strategy="conservative"
                )
                result["compressed"]["system_prompt"] = compressed_system
                result["compressed"]["system_prompt_changes"] = changes
            
            result["optimized"] = True
            
            # Recalculate with compressed versions
            new_token_count = self.analyze_context_usage(
                result["compressed"].get("system_prompt", system_prompt),
                user_prompt,
                result["compressed"].get("context", context),
                max_response_tokens
            )
            result["new_token_count"] = new_token_count
            result["new_budget_check"] = self.check_budget(new_token_count, limit)
        
        return result
    
    def simulate_context_window(
        self,
        prompts: List[str],
        model: str,
        show_warnings: bool = True
    ) -> Dict[str, Any]:
        """
        Simulate how prompts would fit in a model's context window.
        
        Args:
            prompts: List of prompts/messages to simulate
            model: Model to simulate for
            show_warnings: Whether to show warnings
            
        Returns:
            Simulation results
        """
        limit = self._get_context_limit(model)
        
        results = {
            "model": model,
            "context_limit": limit,
            "prompts_tested": len(prompts),
            "results": [],
            "warnings": []
        }
        
        cumulative_tokens = 0
        
        for i, prompt in enumerate(prompts):
            tokens = self.count_tokens(prompt)
            cumulative_tokens += tokens
            
            fits = cumulative_tokens <= limit
            percentage = (cumulative_tokens / limit) * 100
            
            prompt_result = {
                "index": i,
                "tokens": tokens,
                "cumulative_tokens": cumulative_tokens,
                "fits": fits,
                "percentage_used": percentage,
                "remaining": limit - cumulative_tokens
            }
            
            results["results"].append(prompt_result)
            
            if show_warnings:
                if not fits:
                    results["warnings"].append(
                        f"Prompt {i} exceeds context window (total: {cumulative_tokens} tokens)"
                    )
                elif percentage > 90:
                    results["warnings"].append(
                        f"After prompt {i}: Using {percentage:.1f}% of context window"
                    )
        
        results["final_usage"] = {
            "total_tokens": cumulative_tokens,
            "percentage": (cumulative_tokens / limit) * 100,
            "fits_in_context": cumulative_tokens <= limit
        }
        
        return results


# Convenience functions
def count_tokens(text: str, model: str = "grok-beta") -> int:
    """Quick token count."""
    manager = ContextWindowManager(model)
    return manager.count_tokens(text)


def check_fits(text: str, model: str = "grok-beta") -> bool:
    """Check if text fits in model's context window."""
    manager = ContextWindowManager(model)
    tokens = manager.count_tokens(text)
    return tokens <= manager.context_limit
