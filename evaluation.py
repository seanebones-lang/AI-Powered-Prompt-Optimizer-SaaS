"""
Evaluation utilities for prompt optimization.
Includes scoring functions and quality metrics.
"""
import re
from typing import Dict, List, Tuple


def calculate_perplexity_score(text: str) -> float:
    """
    Calculate a simple perplexity-like score (lower is better).
    This is a simplified heuristic - real perplexity requires a language model.
    
    Args:
        text: Text to evaluate
    
    Returns:
        Score (lower = better)
    """
    if not text:
        return 100.0
    
    # Simple heuristic: shorter, more focused text is better
    words = text.split()
    avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
    
    # Simple scoring (can be enhanced)
    score = 50.0  # Base score
    if len(words) > 20:
        score += 10
    if avg_word_length > 6:
        score += 5
    
    return min(100.0, score)


def extract_quality_indicators(text: str) -> Dict[str, any]:
    """
    Extract quality indicators from text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary of quality indicators
    """
    indicators = {
        "word_count": len(text.split()),
        "char_count": len(text),
        "sentence_count": len(re.findall(r'[.!?]+', text)),
        "avg_word_length": sum(len(word) for word in text.split()) / len(text.split()) if text.split() else 0,
        "has_specific_instructions": bool(re.search(r'(should|must|need to|please|specify)', text, re.IGNORECASE)),
        "has_examples": bool(re.search(r'(example|for instance|such as)', text, re.IGNORECASE)),
        "has_formatting": bool(re.search(r'(format|structure|layout|output)', text, re.IGNORECASE)),
    }
    
    return indicators


def compare_prompts(
    original: str,
    optimized: str
) -> Dict[str, any]:
    """
    Compare original and optimized prompts.
    
    Args:
        original: Original prompt
        optimized: Optimized prompt
    
    Returns:
        Comparison metrics
    """
    orig_indicators = extract_quality_indicators(original)
    opt_indicators = extract_quality_indicators(optimized)
    
    improvements = {
        "specificity_increase": opt_indicators["has_specific_instructions"] and not orig_indicators["has_specific_instructions"],
        "examples_added": opt_indicators["has_examples"] and not orig_indicators["has_examples"],
        "formatting_added": opt_indicators["has_formatting"] and not orig_indicators["has_formatting"],
        "length_change": opt_indicators["word_count"] - orig_indicators["word_count"],
    }
    
    return {
        "original": orig_indicators,
        "optimized": opt_indicators,
        "improvements": improvements
    }


def validate_optimization_result(result: Dict[str, any]) -> Tuple[bool, List[str]]:
    """
    Validate an optimization result.
    
    Args:
        result: Optimization result dictionary
    
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    required_fields = ["original_prompt", "optimized_prompt"]
    for field in required_fields:
        if field not in result or not result[field]:
            errors.append(f"Missing required field: {field}")
    
    if "quality_score" in result:
        score = result["quality_score"]
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            errors.append(f"Invalid quality score: {score}")
    
    return len(errors) == 0, errors
