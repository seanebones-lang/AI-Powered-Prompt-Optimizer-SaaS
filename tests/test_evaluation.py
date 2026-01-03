"""
Tests for evaluation utilities.
"""
import pytest
from evaluation import (
    calculate_perplexity_score,
    extract_quality_indicators,
    compare_prompts,
    validate_optimization_result
)


def test_calculate_perplexity_score():
    """Test perplexity score calculation."""
    # Test with text
    score = calculate_perplexity_score("This is a test sentence with multiple words.")
    assert isinstance(score, float)
    assert 0 <= score <= 100
    
    # Test empty text
    score = calculate_perplexity_score("")
    assert score == 100.0


def test_extract_quality_indicators():
    """Test quality indicator extraction."""
    text = "This is a test prompt. It should have specific instructions. For example, use this format."
    
    indicators = extract_quality_indicators(text)
    
    assert "word_count" in indicators
    assert "char_count" in indicators
    assert "sentence_count" in indicators
    assert "avg_word_length" in indicators
    assert indicators["word_count"] > 0
    assert indicators["has_specific_instructions"] is True
    assert indicators["has_examples"] is True


def test_compare_prompts():
    """Test prompt comparison."""
    original = "Write a blog post"
    optimized = "Write a comprehensive blog post about AI technology. Include specific examples and use a clear structure."
    
    comparison = compare_prompts(original, optimized)
    
    assert "original" in comparison
    assert "optimized" in comparison
    assert "improvements" in comparison
    assert comparison["improvements"]["length_change"] > 0


def test_validate_optimization_result():
    """Test optimization result validation."""
    # Valid result
    result = {
        "original_prompt": "Test",
        "optimized_prompt": "Optimized test",
        "quality_score": 85
    }
    
    is_valid, errors = validate_optimization_result(result)
    assert is_valid is True
    assert len(errors) == 0
    
    # Missing field
    result = {
        "original_prompt": "Test"
    }
    
    is_valid, errors = validate_optimization_result(result)
    assert is_valid is False
    assert len(errors) > 0
    
    # Invalid score
    result = {
        "original_prompt": "Test",
        "optimized_prompt": "Optimized",
        "quality_score": 150  # Invalid
    }
    
    is_valid, errors = validate_optimization_result(result)
    assert is_valid is False
