"""
Tests for multi-agent system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents import (
    OrchestratorAgent,
    DeconstructorAgent,
    DiagnoserAgent,
    DesignerAgent,
    EvaluatorAgent,
    PromptType,
    AgentOutput
)


@pytest.fixture
def mock_grok_api():
    """Mock Grok API responses."""
    mock_response = {
        "content": "Test response content",
        "usage": {
            "total_tokens": 100,
            "prompt_tokens": 50,
            "completion_tokens": 50
        },
        "model": "grok-4.1-fast",
        "finish_reason": "stop"
    }
    
    with patch('agents.grok_api') as mock_api:
        mock_api.generate_completion.return_value = mock_response
        yield mock_api


def test_prompt_type_enum():
    """Test PromptType enum values."""
    assert PromptType.CREATIVE.value == "creative"
    assert PromptType.TECHNICAL.value == "technical"
    assert PromptType.ANALYTICAL.value == "analytical"
    assert PromptType.EDUCATIONAL.value == "educational"
    assert PromptType.MARKETING.value == "marketing"


def test_deconstructor_agent(mock_grok_api):
    """Test DeconstructorAgent."""
    agent = DeconstructorAgent()
    assert agent.name == "Deconstructor"
    
    result = agent.process("Test prompt", PromptType.CREATIVE)
    
    assert isinstance(result, AgentOutput)
    assert result.success is True
    assert result.content == "Test response content"
    assert "tokens_used" in result.metadata
    mock_grok_api.generate_completion.assert_called_once()


def test_diagnoser_agent(mock_grok_api):
    """Test DiagnoserAgent."""
    agent = DiagnoserAgent()
    assert agent.name == "Diagnoser"
    
    result = agent.process(
        "Test prompt",
        "Deconstruction content",
        PromptType.TECHNICAL
    )
    
    assert isinstance(result, AgentOutput)
    assert result.success is True
    mock_grok_api.generate_completion.assert_called_once()


def test_designer_agent(mock_grok_api):
    """Test DesignerAgent."""
    agent = DesignerAgent()
    assert agent.name == "Designer"
    
    result = agent.process(
        "Original prompt",
        "Deconstruction",
        "Diagnosis",
        PromptType.MARKETING
    )
    
    assert isinstance(result, AgentOutput)
    assert result.success is True
    mock_grok_api.generate_completion.assert_called_once()


def test_evaluator_agent(mock_grok_api):
    """Test EvaluatorAgent."""
    agent = EvaluatorAgent()
    assert agent.name == "Evaluator"
    
    # Mock response with score
    mock_grok_api.generate_completion.return_value = {
        "content": "Overall score: 85/100",
        "usage": {"total_tokens": 100},
        "model": "grok-4.1-fast"
    }
    
    result = agent.process(
        "Original prompt",
        "Optimized prompt",
        "Sample output",
        PromptType.CREATIVE
    )
    
    assert isinstance(result, AgentOutput)
    assert result.success is True
    assert "quality_score" in result.metadata


def test_evaluator_score_extraction():
    """Test score extraction from evaluator output."""
    agent = EvaluatorAgent()
    
    # Test various score patterns
    assert agent._extract_score("score: 85") == 85
    assert agent._extract_score("85/100") == 85
    assert agent._extract_score("overall: 90") == 90
    assert agent._extract_score("total 75") == 75
    assert agent._extract_score("no score here") == 75  # Default


def test_orchestrator_agent_initialization():
    """Test OrchestratorAgent initialization."""
    orchestrator = OrchestratorAgent()
    
    assert orchestrator.name == "Orchestrator"
    assert orchestrator.deconstructor is not None
    assert orchestrator.diagnoser is not None
    assert orchestrator.designer is not None
    assert orchestrator.evaluator is not None


def test_orchestrator_optimize_prompt(mock_grok_api):
    """Test full optimization workflow."""
    # Mock all agent responses
    mock_grok_api.generate_completion.return_value = {
        "content": "Test content",
        "usage": {"total_tokens": 100},
        "model": "grok-4.1-fast"
    }
    
    mock_grok_api.generate_optimized_output.return_value = "Sample output"
    
    orchestrator = OrchestratorAgent()
    results = orchestrator.optimize_prompt(
        "Test prompt",
        PromptType.CREATIVE
    )
    
    assert results is not None
    assert results["original_prompt"] == "Test prompt"
    assert results["prompt_type"] == "creative"
    assert "deconstruction" in results
    assert "diagnosis" in results
    assert "optimized_prompt" in results
    assert "sample_output" in results


def test_orchestrator_handles_errors(mock_grok_api):
    """Test orchestrator handles errors gracefully."""
    # Mock API to raise error
    mock_grok_api.generate_completion.side_effect = Exception("API Error")
    
    orchestrator = OrchestratorAgent()
    results = orchestrator.optimize_prompt(
        "Test prompt",
        PromptType.TECHNICAL
    )
    
    assert results is not None
    assert len(results.get("errors", [])) > 0


def test_orchestrator_identity_query(mock_grok_api):
    """Test identity query handling."""
    mock_grok_api.handle_identity_query.return_value = "I am NextEleven AI"
    
    orchestrator = OrchestratorAgent()
    response = orchestrator.handle_identity_query("Who are you?")
    
    assert response == "I am NextEleven AI"
    mock_grok_api.handle_identity_query.assert_called_once_with("Who are you?")


def test_agent_output_model():
    """Test AgentOutput Pydantic model."""
    output = AgentOutput(
        success=True,
        content="Test content",
        metadata={"key": "value"},
        errors=[]
    )
    
    assert output.success is True
    assert output.content == "Test content"
    assert output.metadata == {"key": "value"}
    assert output.errors == []


def test_orchestrator_extract_optimized_prompt():
    """Test optimized prompt extraction."""
    orchestrator = OrchestratorAgent()
    
    # Test with "Optimized Prompt:" marker
    design_output = """Here's the optimized prompt:

Optimized Prompt:
This is the optimized version

Explanation:
This is better because..."""
    
    extracted = orchestrator._extract_optimized_prompt(design_output)
    assert "optimized" in extracted.lower() or "This is the optimized version" in extracted
    
    # Test fallback
    simple_output = "This is a simple optimized prompt without markers."
    extracted = orchestrator._extract_optimized_prompt(simple_output)
    assert len(extracted) > 0
