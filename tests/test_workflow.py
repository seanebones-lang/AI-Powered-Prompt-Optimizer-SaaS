"""
Tests for enhanced agent workflow system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents import (
    OrchestratorAgent,
    AgentWorkflow,
    PromptType,
    DeconstructorAgent,
    DiagnoserAgent
)


def test_agent_workflow_initialization():
    """Test AgentWorkflow initialization."""
    agents = {
        'deconstructor': DeconstructorAgent(),
        'diagnoser': DiagnoserAgent()
    }
    workflow = AgentWorkflow(agents)
    
    assert workflow.agents == agents
    assert workflow.max_workers == 3


def test_workflow_should_use_parallel():
    """Test parallel execution decision logic."""
    agents = {'test': Mock()}
    workflow = AgentWorkflow(agents)
    
    # Creative prompts should use parallel
    assert workflow.should_use_parallel(PromptType.CREATIVE, 100) is True
    
    # Technical prompts should use parallel
    assert workflow.should_use_parallel(PromptType.TECHNICAL, 100) is True
    
    # Long prompts should use parallel
    assert workflow.should_use_parallel(PromptType.MARKETING, 600) is True
    
    # Short marketing prompts should not
    assert workflow.should_use_parallel(PromptType.MARKETING, 100) is False


def test_workflow_retry_logic():
    """Test retry logic execution."""
    agents = {'test': Mock()}
    workflow = AgentWorkflow(agents)
    
    # Mock function that fails twice then succeeds
    call_count = [0]
    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Temporary error")
        return "Success"
    
    result = workflow._execute_with_retry(flaky_func, max_retries=3, retry_delay=0.1)
    assert result == "Success"
    assert call_count[0] == 3


def test_workflow_retry_exhaustion():
    """Test retry logic when all attempts fail."""
    agents = {'test': Mock()}
    workflow = AgentWorkflow(agents)
    
    def failing_func():
        raise Exception("Persistent error")
    
    with pytest.raises(Exception):
        workflow._execute_with_retry(failing_func, max_retries=2, retry_delay=0.1)


def test_orchestrator_workflow_initialization():
    """Test OrchestratorAgent includes workflow."""
    orchestrator = OrchestratorAgent()
    
    assert hasattr(orchestrator, 'workflow')
    assert isinstance(orchestrator.workflow, AgentWorkflow)
    assert orchestrator.workflow.agents is not None


def test_orchestrator_parallel_mode():
    """Test orchestrator parallel mode execution."""
    orchestrator = OrchestratorAgent()
    
    with patch.object(orchestrator.deconstructor, 'process') as mock_deconstruct:
        with patch.object(orchestrator.diagnoser, 'process') as mock_diagnose:
            with patch.object(orchestrator.designer, 'process') as mock_design:
                with patch('agents.grok_api') as mock_api:
                    mock_deconstruct.return_value = Mock(
                        success=True,
                        content="Deconstruction",
                        errors=[]
                    )
                    mock_diagnose.return_value = Mock(
                        success=True,
                        content="Diagnosis",
                        errors=[]
                    )
                    mock_design.return_value = Mock(
                        success=True,
                        content="Optimized Prompt",
                        errors=[]
                    )
                    mock_api.generate_optimized_output.return_value = "Sample output"
                    
                    results = orchestrator.optimize_prompt(
                        "Test prompt",
                        PromptType.CREATIVE,
                        use_parallel=True
                    )
                    
                    assert results["workflow_mode"] == "parallel"
                    assert results["original_prompt"] == "Test prompt"


def test_orchestrator_sequential_mode():
    """Test orchestrator sequential mode execution."""
    orchestrator = OrchestratorAgent()
    
    with patch.object(orchestrator.deconstructor, 'process') as mock_deconstruct:
        with patch.object(orchestrator.diagnoser, 'process') as mock_diagnose:
            with patch.object(orchestrator.designer, 'process') as mock_design:
                with patch('agents.grok_api') as mock_api:
                    mock_deconstruct.return_value = Mock(
                        success=True,
                        content="Deconstruction",
                        errors=[]
                    )
                    mock_diagnose.return_value = Mock(
                        success=True,
                        content="Diagnosis",
                        errors=[]
                    )
                    mock_design.return_value = Mock(
                        success=True,
                        content="Optimized Prompt",
                        errors=[]
                    )
                    mock_api.generate_optimized_output.return_value = "Sample output"
                    
                    results = orchestrator.optimize_prompt(
                        "Test prompt",
                        PromptType.MARKETING,
                        use_parallel=False
                    )
                    
                    assert results["workflow_mode"] == "sequential"


def test_orchestrator_auto_detect_mode():
    """Test orchestrator auto-detection of workflow mode."""
    orchestrator = OrchestratorAgent()
    
    # Creative prompt should auto-detect parallel
    with patch.object(orchestrator, 'optimize_prompt') as mock_optimize:
        # This will test the should_use_parallel logic
        workflow = orchestrator.workflow
        assert workflow.should_use_parallel(PromptType.CREATIVE, 100) is True
        assert workflow.should_use_parallel(PromptType.MARKETING, 100) is False


def test_preliminary_diagnosis():
    """Test preliminary diagnosis method."""
    orchestrator = OrchestratorAgent()
    
    with patch('agents.grok_api') as mock_api:
        mock_api.generate_completion.return_value = {
            "content": "Preliminary analysis",
            "usage": {"total_tokens": 100},
            "model": "grok-4.1-fast"
        }
        
        result = orchestrator._diagnose_preliminary("Test prompt", PromptType.TECHNICAL)
        
        assert result.success is True
        assert "preliminary" in result.metadata


def test_workflow_error_handling():
    """Test workflow error handling and fallback."""
    orchestrator = OrchestratorAgent()
    
    # Test that errors are caught and included in results
    with patch.object(orchestrator.deconstructor, 'process') as mock_deconstruct:
        mock_deconstruct.side_effect = Exception("API Error")
        
        results = orchestrator.optimize_prompt(
            "Test prompt",
            PromptType.CREATIVE
        )
        
        assert len(results.get("errors", [])) > 0
        assert results["deconstruction"] is None
