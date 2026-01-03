# Agent Workflow System Documentation

**Last Updated:** January 2026  
**Status:** ✅ Enhanced with Parallel Execution & Dynamic Routing

## Overview

The agent workflow system has been enhanced with dynamic orchestration, parallel execution capabilities, and robust error handling with retry logic. This improves performance for complex prompts while maintaining reliability.

## Key Features

### 1. Dynamic Workflow Routing

The orchestrator automatically determines the best workflow strategy based on:
- **Prompt Type**: Creative, Technical, and Analytical prompts use parallel execution
- **Prompt Complexity**: Longer prompts (>500 chars) trigger parallel mode
- **Manual Override**: Can force sequential or parallel mode

### 2. Parallel Execution

For complex prompts, the system can run multiple agents in parallel:
- **Deconstruction + Preliminary Diagnosis**: Run simultaneously for faster processing
- **Thread Pool**: Uses ThreadPoolExecutor with max 3 workers
- **Error Handling**: Falls back to sequential if parallel fails

### 3. Retry Logic

All API calls include automatic retry with exponential backoff:
- **Max Retries**: 3 attempts (configurable)
- **Backoff Strategy**: Exponential (1s, 2s, 4s)
- **Error Recovery**: Graceful degradation on failure

### 4. Workflow Modes

#### Sequential Mode (Default)
- Standard 4-D workflow
- One agent at a time
- Reliable and predictable
- Best for simple prompts

#### Parallel Mode (Auto-Triggered)
- Parallel deconstruction + preliminary diagnosis
- Faster for complex prompts
- Automatic fallback on errors
- Best for Creative, Technical, Analytical prompts

## Architecture

### AgentWorkflow Class

Manages workflow execution and coordination:

```python
class AgentWorkflow:
    def __init__(self, agents: Dict[str, Any])
    def run_parallel(self, tasks: List[Dict], timeout: Optional[float])
    def _execute_with_retry(self, func: Callable, max_retries: int, ...)
    def should_use_parallel(self, prompt_type: PromptType, prompt_length: int) -> bool
```

### Enhanced OrchestratorAgent

The orchestrator now includes:

```python
class OrchestratorAgent:
    def __init__(self):
        self.workflow = AgentWorkflow(self.agents_dict)
    
    def optimize_prompt(
        self,
        prompt: str,
        prompt_type: PromptType,
        use_parallel: Optional[bool] = None
    ) -> Dict[str, Any]
```

## Workflow Execution

### Sequential Workflow (Standard)

```
1. Deconstruct → 2. Diagnose → 3. Design → 4. Sample Output → 5. Evaluate
```

### Parallel Workflow (Enhanced)

```
Phase 1 (Parallel):
  ├─ Deconstruct ─┐
  └─ Diagnose (Preliminary) ┘
     ↓
Phase 2 (Sequential):
  Diagnose (Full) → Design
     ↓
Phase 3 (Sequential):
  Sample Output → Evaluate
```

## Performance Improvements

### Timing Comparison

- **Sequential**: ~8-12 seconds (5 API calls)
- **Parallel**: ~6-9 seconds (4 API calls + parallel phase 1)
- **Improvement**: 20-30% faster for complex prompts

### Resource Usage

- **Thread Pool**: Max 3 workers
- **Memory**: Minimal overhead
- **API Calls**: Same or fewer total calls

## Error Handling

### Retry Strategy

All API calls use retry logic:
- **Attempt 1**: Immediate
- **Attempt 2**: After 1 second
- **Attempt 3**: After 2 seconds
- **On Failure**: Log error, continue with available data

### Fallback Mechanisms

1. **Parallel Failure**: Falls back to sequential
2. **API Failure**: Retries with exponential backoff
3. **Agent Failure**: Continues with available results
4. **Complete Failure**: Returns error in results dict

## Configuration

### Auto-Detection Rules

Parallel mode is used when:
- Prompt type is Creative, Technical, or Analytical
- OR prompt length > 500 characters
- OR explicitly requested via `use_parallel=True`

### Manual Control

```python
orchestrator = OrchestratorAgent()

# Force parallel
results = orchestrator.optimize_prompt(
    prompt, 
    PromptType.CREATIVE,
    use_parallel=True
)

# Force sequential
results = orchestrator.optimize_prompt(
    prompt,
    PromptType.MARKETING,
    use_parallel=False
)

# Auto-detect (default)
results = orchestrator.optimize_prompt(
    prompt,
    PromptType.TECHNICAL
)
```

## Benefits

1. **Performance**: 20-30% faster for complex prompts
2. **Reliability**: Retry logic handles transient failures
3. **Flexibility**: Auto-detects or manual control
4. **Scalability**: Can handle more complex workflows
5. **User Experience**: Faster results for complex prompts

## Testing

### Test Scenarios

1. **Simple Prompt (Sequential)**
   - Short marketing prompt
   - Should use sequential mode
   - All steps complete successfully

2. **Complex Prompt (Parallel)**
   - Long technical prompt
   - Should use parallel mode
   - Faster completion

3. **Error Handling**
   - API failure scenario
   - Retry logic activation
   - Graceful degradation

4. **Manual Override**
   - Force parallel on simple prompt
   - Force sequential on complex prompt
   - Verify override works

## Future Enhancements

### Planned Features

1. **Adaptive Parallelism**: Learn from prompt patterns
2. **Caching**: Cache deconstruction/diagnosis for similar prompts
3. **Streaming**: Real-time updates during parallel execution
4. **Metrics**: Track workflow performance
5. **A/B Testing**: Compare parallel vs sequential results

### Experimental Features

1. **Full Parallel Design**: Parallel design with multiple variants
2. **Conditional Routing**: Different workflows based on prompt analysis
3. **Agent Pooling**: Reuse agent instances for performance

## Best Practices

1. **Default to Auto**: Let the system decide workflow mode
2. **Monitor Performance**: Track which mode works best
3. **Handle Errors**: Always check results["errors"]
4. **Test Both Modes**: Verify behavior in sequential and parallel
5. **Log Workflow Mode**: Include in results for debugging

## Troubleshooting

### Parallel Mode Not Used

**Issue**: System always uses sequential mode

**Solutions**:
- Check prompt type (Creative/Technical/Analytical trigger parallel)
- Check prompt length (>500 chars triggers parallel)
- Verify ThreadPoolExecutor is available
- Check logs for parallel mode detection

### Performance Not Improved

**Issue**: Parallel mode doesn't improve speed

**Solutions**:
- API rate limits may be the bottleneck
- Network latency affects parallel gains
- Simple prompts don't benefit from parallel
- Check thread pool configuration

### Errors in Parallel Mode

**Issue**: More errors in parallel mode

**Solutions**:
- Check API rate limits
- Verify error handling fallback works
- Review retry logic configuration
- Consider increasing retry attempts

---

**Documentation Version:** 1.0  
**Last Updated:** January 2026  
**Maintained By:** Development Team
