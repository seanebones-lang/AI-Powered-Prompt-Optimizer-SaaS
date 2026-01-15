"""
Multi-agent system for prompt optimization.
Implements Lyra's 4-D methodology: Deconstruct, Diagnose, Design, Deliver.
Each agent has a specific role with clear schemas and error handling.

Enhanced with dynamic workflow orchestration, parallel execution, and retry logic.
"""
import logging
import time
import re
import json
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from api_utils import grok_api
from collections_utils import enable_collections_for_agent, is_collections_enabled
from config import settings
from agentic_rag import retrieve_prompt_examples, is_agentic_rag_enabled
from cache_utils import get_cached_response, cache_response

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for agent execution tracking."""
    agent_name: str
    execution_time_ms: float
    tokens_used: int
    success: bool
    error: Optional[str] = None


class StructuredOutputParser:
    """
    Parse and validate structured outputs from agent responses.

    Handles JSON extraction, validation, and fallback parsing.
    """

    @staticmethod
    def extract_json(content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from agent response content.

        Handles both raw JSON and markdown code blocks.
        """
        if not content:
            return None

        # Try direct JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_patterns = [
            r'```json\s*\n?(.*?)\n?```',
            r'```\s*\n?(.*?)\n?```',
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        ]

        for pattern in json_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if '```' in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue

        return None

    @staticmethod
    def extract_score(content: str) -> int:
        """Extract quality score from content using multiple patterns."""
        if not content:
            return 75

        content_lower = content.lower()
        patterns = [
            r'(?:total|overall|final|quality)\s*(?:score)?[:\s]+(\d+)',
            r'(\d+)\s*/\s*100',
            r'score[:\s]+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content_lower)
            if match:
                score = int(match.group(1))
                return max(0, min(100, score))

        return 75  # Default score


class PromptType(str, Enum):
    """Supported prompt types."""
    BUILD_AGENT = "build_agent"
    REQUEST_BUILD = "request_build"
    DEPLOYMENT_OPTIONS = "deployment_options"
    SYSTEM_IMPROVEMENT = "system_improvement"


class AgentOutput(BaseModel):
    """Standard output format for all agents."""
    success: bool = Field(description="Whether the operation was successful")
    content: str = Field(description="The main output content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class BaseAgent:
    """
    Base class for all agents in the 4-D optimization system.

    Provides common functionality for API calls, error handling,
    and output formatting.
    """

    name: str = "BaseAgent"
    role: str = "Base agent"
    default_temperature: float = 0.5
    default_max_tokens: int = 1500

    async def _call_api(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None
    ) -> AgentOutput:
        # Check cache before making API call
        cache_key = f"{self.name}:{user_prompt}:{system_prompt}"
        cached_response = get_cached_response(cache_key, self.name)
        if cached_response:
            return AgentOutput(
                success=cached_response['success'],
                content=cached_response['content'],
                metadata=cached_response['metadata'],
                errors=cached_response.get('errors', [])
            )

        """
        Common API call method with error handling and metrics.

        Args:
            user_prompt: The user prompt to send
            system_prompt: The system prompt for context
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            tools: Optional tools for the API call

        Returns:
            AgentOutput with success status, content, and metrics
        """
        start_time = time.time()
        try:
            response = grok_api.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                tools=tools
            )

            execution_time_ms = (time.time() - start_time) * 1000
            tokens_used = response["usage"]["total_tokens"]

            output = AgentOutput(
                success=True,
                content=response["content"],
                metadata={
                    "tokens_used": tokens_used,
                    "model": response["model"],
                    "agent": self.name,
                    "execution_time_ms": round(execution_time_ms, 2)
                }
            )
            # Cache the successful response
            cache_response(cache_key, self.name, {
                'success': output.success,
                'content': output.content,
                'metadata': output.metadata,
                'errors': output.errors
            })
            return output
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"{self.name} error: {str(e)}")
            return AgentOutput(
                success=False,
                content="",
                errors=[str(e)],
                metadata={
                    "agent": self.name,
                    "execution_time_ms": round(execution_time_ms, 2)
                }
            )

    def _get_prompt_type_context(self, prompt_type: PromptType) -> str:
        """Get type-specific context for prompts."""
        contexts = {
            # Agent Development
            PromptType.SYSTEM_PROMPT: "Focus on creating effective system prompts for AI agents with clear instructions, constraints, and behavior guidelines.",
            PromptType.AGENT_PERSONA: "Focus on developing detailed agent personas, personality traits, communication styles, and behavioral patterns.",
            PromptType.TOOL_DEFINITION: "Focus on defining tool specifications, parameters, error handling, and integration requirements.",
            PromptType.MULTI_AGENT_WORKFLOW: "Focus on designing orchestration patterns for multiple agents working together.",

            # Build Planning
            PromptType.BUILD_PLAN: "Focus on creating comprehensive project specifications, requirements, timelines, and implementation strategies.",
            PromptType.ARCHITECTURE: "Focus on system design, component relationships, data flows, and technical architecture decisions.",
            PromptType.API_DESIGN: "Focus on API specifications, endpoints, data models, authentication, and integration patterns.",

            # Code & Technical
            PromptType.CODE_GENERATION: "Focus on generating high-quality, maintainable code with proper error handling and documentation.",
            PromptType.CODE_REVIEW: "Focus on identifying code quality issues, security vulnerabilities, and improvement opportunities.",
            PromptType.DOCUMENTATION: "Focus on creating clear, comprehensive documentation for users and developers.",

            # Reasoning Modes
            PromptType.CHAIN_OF_THOUGHT: "Focus on step-by-step reasoning processes and logical problem-solving approaches.",
            PromptType.TREE_OF_THOUGHT: "Focus on exploring multiple solution paths and evaluating different approaches.",
            PromptType.REFLECTION: "Focus on self-critique, improvement strategies, and learning from past experiences."
        }
        return contexts.get(prompt_type, "")


class DeconstructorAgent(BaseAgent):
    """Agent responsible for deconstructing vague inputs into structured components."""

    name = "Deconstructor"
    role = "Break down vague or unstructured prompts into clear, analyzable components"
    default_temperature = 0.5

    async def process(self, prompt: str, prompt_type: PromptType) -> AgentOutput:
        """Deconstruct a prompt into components."""
        system_prompt = f"""As NextEleven AI's Deconstructor specialist, your role is to break down vague or unstructured prompts into clear, analyzable components.

Analyze the following {prompt_type.value} prompt and identify:
1. Core intent/purpose
2. Key entities and concepts
3. Desired output format
4. Missing information or ambiguities
5. Context requirements

{self._get_prompt_type_context(prompt_type)}

Provide a structured breakdown in a clear, organized format."""

        user_prompt = f"Deconstruct the following prompt:\n\n{prompt}"

        return self._call_api(user_prompt, system_prompt)


class DiagnoserAgent(BaseAgent):
    """Agent responsible for diagnosing issues in prompts."""

    name = "Diagnoser"
    role = "Identify weaknesses, ambiguities, and potential issues in prompts"
    default_temperature = 0.4

    async def process(self, prompt: str, deconstruction: str, prompt_type: PromptType) -> AgentOutput:
        """Diagnose issues in a prompt."""
        system_prompt = f"""As NextEleven AI's Diagnoser specialist, your role is to identify weaknesses and issues in prompts.

Analyze the prompt and its deconstruction to identify:
1. Ambiguities and unclear instructions
2. Missing context or information
3. Potential misinterpretations
4. Lack of specificity
5. Formatting or structure issues
6. Best practices violations

{self._get_prompt_type_context(prompt_type)}"""

        user_prompt = f"""Original Prompt:
{prompt}

Deconstruction:
{deconstruction}

Identify all issues and weaknesses in this prompt. Be specific and actionable."""

        return self._call_api(user_prompt, system_prompt)


class DesignerAgent(BaseAgent):
    """Agent responsible for designing refined, optimized prompts."""

    name = "Designer"
    role = "Create refined, optimized prompts based on deconstruction and diagnosis"
    default_temperature = 0.6
    default_max_tokens = 2000

    async def process(
        self,
        prompt: str,
        deconstruction: str,
        diagnosis: str,
        prompt_type: PromptType
    ) -> AgentOutput:
        """Design an optimized prompt."""
        system_prompt = f"""As NextEleven AI's Designer specialist, your role is to create refined, optimized prompts that address all identified issues.

Design an improved version of the prompt that:
1. Eliminates ambiguities
2. Adds necessary context
3. Specifies desired output format
4. Includes best practices for {prompt_type.value} prompts
5. Maintains the original intent
6. Improves clarity and actionability

{self._get_prompt_type_context(prompt_type)}

Provide the optimized prompt and explain key improvements."""

        user_prompt = f"""Original Prompt:
{prompt}

Deconstruction:
{deconstruction}

Diagnosis:
{diagnosis}

Design an optimized version of this prompt. Include both the optimized prompt and a brief explanation of improvements."""

        # Try Agentic RAG first if enabled (more advanced retrieval)
        rag_examples = None
        if is_agentic_rag_enabled():
            logger.info("Using Agentic RAG for prompt example retrieval")
            rag_examples = retrieve_prompt_examples(
                prompt_type=prompt_type.value,
                original_prompt=prompt,
                max_examples=3
            )
            if rag_examples:
                user_prompt += f"""

Reference Examples (from knowledge base):
{rag_examples}

Use these examples as inspiration while creating the optimized prompt."""

        # Fallback to Collections search if configured and enabled
        tools = None
        if not rag_examples and settings.enable_collections and is_collections_enabled():
            tools = enable_collections_for_agent(prompt_type.value, include_collections=True)
            if tools:
                system_prompt += f"""

You have access to a knowledge base of high-quality prompt examples via the file_search tool.
When designing the optimized prompt, search for similar {prompt_type.value} prompt examples that demonstrate best practices.
Use the file_search tool to:
1. Find examples of well-structured prompts in this domain
2. Identify patterns and techniques used in high-quality prompts
3. Reference successful prompt structures when creating the optimized version

The tool will search through curated collections of prompt examples. Use it proactively to enhance your design."""

        return self._call_api(user_prompt, system_prompt, tools=tools)


class EvaluatorAgent(BaseAgent):
    """Agent responsible for evaluating and scoring prompt quality."""

    name = "Evaluator"
    role = "Evaluate prompt quality and provide scores"
    default_temperature = 0.3

    async def process(
        self,
        original_prompt: str,
        optimized_prompt: str,
        sample_output: str,
        prompt_type: PromptType
    ) -> AgentOutput:
        """Evaluate prompt quality and generate a score."""
        system_prompt = """As NextEleven AI's Evaluator specialist, your role is to assess prompt quality on multiple dimensions.

Evaluate both prompts on:
1. Clarity and specificity (0-25 points)
2. Completeness and context (0-25 points)
3. Actionability and structure (0-25 points)
4. Likely output quality (0-25 points)

Provide scores for both original and optimized prompts, plus an overall improvement assessment."""

        user_prompt = f"""Original Prompt:
{original_prompt}

Optimized Prompt:
{optimized_prompt}

Sample Output from Optimized Prompt:
{sample_output}

Evaluate both prompts and provide detailed scores (0-100 total) for each dimension."""

        result = self._call_api(user_prompt, system_prompt)

        # Extract score and add to metadata
        if result.success:
            score = self._extract_score(result.content.lower())
            result.metadata["quality_score"] = score

        return result

    def _extract_score(self, content: str) -> int:
        """Extract quality score from evaluator output (simple heuristic)."""
        import re
        patterns = [
            r'score[:\s]+(\d+)',
            r'(\d+)/100',
            r'overall[:\s]+(\d+)',
            r'total[:\s]+(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                score = int(match.group(1))
                return max(0, min(100, score))

        # Default to 75 if no score found
        return 75


class AgentWorkflow:
    """
    Workflow manager for coordinating agent tasks.
    Supports parallel execution, conditional routing, and error handling.
    """
    
    def __init__(self, agents: Dict[str, Any]):
        """
        Initialize workflow with agents.
        
        Args:
            agents: Dictionary of agent instances
        """
        self.agents = agents
        self.max_workers = 3  # Maximum parallel workers
    
    def run_parallel(
        self,
        tasks: List[Dict[str, Any]],
        timeout: Optional[float] = None
    ) -> List[Any]:
        """
        Execute multiple agent tasks in parallel.
        
        Args:
            tasks: List of task dictionaries with 'agent' and 'input' keys
            timeout: Optional timeout in seconds
        
        Returns:
            List of results in order of completion
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                agent = task.get('agent')
                task.get('input', {})
                func = task.get('func', agent.process)
                args = task.get('args', [])
                kwargs = task.get('kwargs', {})
                
                future = executor.submit(self._execute_with_retry, func, *args, **kwargs)
                future_to_task[future] = task
            
            # Collect results as they complete
            for future in as_completed(future_to_task, timeout=timeout):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append({
                        'task': task.get('name', 'unknown'),
                        'result': result,
                        'success': True
                    })
                except Exception as e:
                    logger.error(f"Parallel task {task.get('name', 'unknown')} failed: {str(e)}")
                    results.append({
                        'task': task.get('name', 'unknown'),
                        'result': None,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result
        
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed: {str(e)}")
        
        raise last_exception
    
    def should_use_parallel(self, prompt_type: PromptType, prompt_length: int) -> bool:
        """
        Determine if parallel execution should be used.
        
        Args:
            prompt_type: Type of prompt
            prompt_length: Length of prompt in characters
        
        Returns:
            True if parallel execution should be used
        """
        # Use parallel for complex prompt types or long prompts
        parallel_types = [PromptType.BUILD_AGENT, PromptType.REQUEST_BUILD]
        return prompt_type in parallel_types or prompt_length > 500


class ChainOfThoughtAgent(BaseAgent):
    """Agent responsible for guiding through a chain of thought process."""
    
    name = "ChainOfThought"
    role = "Guide the user through a step-by-step reasoning process"
    default_temperature = 0.6
    
    async def process(self, prompt: str, prompt_type: PromptType) -> AgentOutput:
        """Process a prompt with chain of thought reasoning."""
        system_prompt = f"""As NextEleven AI's Chain of Thought specialist, your role is to guide the user through a step-by-step reasoning process to solve complex problems.

Focus on breaking down the problem into logical steps, explaining each step clearly.
{self._get_prompt_type_context(prompt_type)}

Provide a structured reasoning process in a clear, organized format."""
        
        user_prompt = f"Guide me through solving this problem with a chain of thought approach:\n\n{prompt}"
        
        return await self._call_api(user_prompt, system_prompt)

class TreeOfThoughtAgent(BaseAgent):
    """Agent responsible for exploring multiple reasoning paths."""
    
    name = "TreeOfThought"
    role = "Explore multiple reasoning paths to find the best solution"
    default_temperature = 0.7
    
    async def process(self, prompt: str, prompt_type: PromptType) -> AgentOutput:
        """Process a prompt with tree of thought reasoning."""
        system_prompt = f"""As NextEleven AI's Tree of Thought specialist, your role is to explore multiple reasoning paths to find the best solution to complex problems.

Focus on generating different approaches or hypotheses, evaluating their pros and cons.
{self._get_prompt_type_context(prompt_type)}

Provide a comprehensive analysis of different thought paths in a clear, organized format."""
        
        user_prompt = f"Explore different solutions to this problem using a tree of thought approach:\n\n{prompt}"
        
        return await self._call_api(user_prompt, system_prompt)

class OrchestratorAgent:
    """
    Orchestrator agent that coordinates the multi-agent workflow.
    
    Enhanced with dynamic workflow routing, parallel execution, and retry logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        from agent_config import AgentConfigManager
        self.config = config or AgentConfigManager.DEFAULT_CONFIG
        
        self.name = "Orchestrator"
        
        # Initialize agents with config
        self.deconstructor = DeconstructorAgent()
        self.deconstructor.default_temperature = self.config.get("deconstructor", {}).get("temperature", 0.5)
        self.deconstructor.default_max_tokens = self.config.get("deconstructor", {}).get("max_tokens", 1500)
        
        self.diagnoser = DiagnoserAgent()
        self.diagnoser.default_temperature = self.config.get("diagnoser", {}).get("temperature", 0.4)
        self.diagnoser.default_max_tokens = self.config.get("diagnoser", {}).get("max_tokens", 1500)
        
        self.designer = DesignerAgent()
        self.designer.default_temperature = self.config.get("designer", {}).get("temperature", 0.8)
        self.designer.default_max_tokens = self.config.get("designer", {}).get("max_tokens", 2000)
        
        self.evaluator = EvaluatorAgent()
        self.evaluator.default_temperature = self.config.get("evaluator", {}).get("temperature", 0.3)
        self.evaluator.default_max_tokens = self.config.get("evaluator", {}).get("max_tokens", 1000)
        
        self.chain_of_thought = ChainOfThoughtAgent()
        self.chain_of_thought.default_temperature = self.config.get("chain_of_thought", {}).get("temperature", 0.6)
        self.chain_of_thought.default_max_tokens = self.config.get("chain_of_thought", {}).get("max_tokens", 1500)
        
        self.tree_of_thought = TreeOfThoughtAgent()
        self.tree_of_thought.default_temperature = self.config.get("tree_of_thought", {}).get("temperature", 0.7)
        self.tree_of_thought.default_max_tokens = self.config.get("tree_of_thought", {}).get("max_tokens", 1500)
        
        # Initialize workflow manager
        self.agents_dict = {
            'deconstructor': self.deconstructor,
            'diagnoser': self.diagnoser,
            'designer': self.designer,
            'evaluator': self.evaluator,
            'chain_of_thought': self.chain_of_thought,
            'tree_of_thought': self.tree_of_thought
        }
        self.workflow = AgentWorkflow(self.agents_dict)
    
    async def optimize_prompt(
        self,
        prompt: str,
        prompt_type: PromptType,
        use_parallel: Optional[bool] = None,
        methodology: str = "4D"
    ) -> Dict[str, Any]:
        """
        Orchestrate the full 4-D optimization workflow with dynamic routing.
        
        Args:
            prompt: User's original prompt
            prompt_type: Type of prompt (creative, technical, etc.)
            use_parallel: Force parallel execution (None = auto-detect)
        
        Returns:
            Dictionary with all outputs from each agent step
        """
        results = {
            "original_prompt": prompt,
            "prompt_type": prompt_type.value,
            "deconstruction": None,
            "diagnosis": None,
            "optimized_prompt": None,
            "sample_output": None,
            "evaluation": None,
            "quality_score": None,
            "errors": [],
            "workflow_mode": "sequential"  # Will be updated if parallel
        }
        
        try:
            # Determine if parallel execution should be used
            if use_parallel is None:
                use_parallel = self.workflow.should_use_parallel(prompt_type, len(prompt))
            
            results["workflow_mode"] = "parallel" if use_parallel else "sequential"
            logger.info(f"Using {results['workflow_mode']} workflow mode for {prompt_type.value} prompt")
            
            # Phase 1: Deconstruct and Diagnose (can be parallel for complex prompts)
            if use_parallel and prompt_type in [PromptType.BUILD_AGENT, PromptType.REQUEST_BUILD]:
                logger.info("Running deconstruction and diagnosis in parallel...")
                parallel_results = self.workflow.run_parallel([
                    {
                        'name': 'deconstruct',
                        'agent': self.deconstructor,
                        'func': self.deconstructor.process,
                        'args': [prompt, prompt_type],
                        'kwargs': {}
                    },
                    {
                        'name': 'diagnose_preliminary',
                        'agent': self.diagnoser,
                        'func': self._diagnose_preliminary,
                        'args': [prompt, prompt_type],
                        'kwargs': {}
                    }
                ])
                
                # Extract results
                deconstruct_result = None
                for pr in parallel_results:
                    if pr['task'] == 'deconstruct' and pr['success']:
                        deconstruct_result = pr['result']
                    elif pr['task'] == 'diagnose_preliminary' and pr['success']:
                        # Preliminary diagnosis can inform full diagnosis
                        pass
                
                if not deconstruct_result or not deconstruct_result.success:
                    # Fallback to sequential
                    logger.warning("Parallel execution failed, falling back to sequential")
                    deconstruct_result = self.deconstructor.process(prompt, prompt_type)
                
                results["deconstruction"] = deconstruct_result.content
                
                # Full diagnosis (needs deconstruction)
                diagnose_result = self.diagnoser.process(
                    prompt,
                    deconstruct_result.content,
                    prompt_type
                )
            else:
                # Sequential execution (default or for simple prompts)
                logger.info("Running sequential workflow...")
                
                # Step 1: Deconstruct
                deconstruct_result = self.deconstructor.process(prompt, prompt_type)
                if not deconstruct_result.success:
                    results["errors"].extend(deconstruct_result.errors)
                    return results
                results["deconstruction"] = deconstruct_result.content
                
                # Step 2: Diagnose
                diagnose_result = self.diagnoser.process(
                    prompt,
                    deconstruct_result.content,
                    prompt_type
                )
            
            if not diagnose_result.success:
                results["errors"].extend(diagnose_result.errors)
                return results
            results["diagnosis"] = diagnose_result.content
            
            # Phase 2: Design (always sequential as it needs both deconstruction and diagnosis)
            # This phase uses Collections RAG if enabled
            logger.info("Starting design phase with Collections RAG support...")
            design_result = self.designer.process(
                prompt,
                deconstruct_result.content,
                diagnose_result.content,
                prompt_type
            )
            if not design_result.success:
                results["errors"].extend(design_result.errors)
                return results
            results["optimized_prompt"] = design_result.content
            
            # Extract just the optimized prompt text (may need refinement)
            optimized_prompt_text = self._extract_optimized_prompt(design_result.content)
            
            # Phase 3: Generate sample output (with retry)
            logger.info("Generating sample output...")
            try:
                sample_output = self.workflow._execute_with_retry(
                    grok_api.generate_optimized_output,
                    optimized_prompt_text,
                    max_retries=2,
                    retry_delay=1.0
                )
                results["sample_output"] = sample_output
            except Exception as e:
                logger.warning(f"Could not generate sample output after retries: {str(e)}")
                results["sample_output"] = "Sample output generation failed."
                results["errors"].append(f"Sample output error: {str(e)}")
            
            # Phase 4: Evaluate (with retry)
            logger.info("Starting evaluation phase...")
            try:
                evaluate_result = self.workflow._execute_with_retry(
                    self.evaluator.process,
                    prompt,
                    optimized_prompt_text,
                    results["sample_output"],
                    prompt_type,
                    max_retries=2,
                    retry_delay=1.0
                )
                if evaluate_result.success:
                    results["evaluation"] = evaluate_result.content
                    results["quality_score"] = evaluate_result.metadata.get("quality_score", 75)
            except Exception as e:
                logger.warning(f"Evaluation failed after retries: {str(e)}")
                results["errors"].append(f"Evaluation error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            results["errors"].append(str(e))
        
        return results
    
    async def _diagnose_preliminary(self, prompt: str, prompt_type: PromptType) -> AgentOutput:
        """
        Preliminary diagnosis that can run in parallel with deconstruction.
        Provides quick insights without full deconstruction context.
        
        Args:
            prompt: Original prompt
            prompt_type: Type of prompt
        
        Returns:
            Preliminary diagnosis output
        """
        try:
            system_prompt = f"""As NextEleven AI's Diagnoser specialist, provide a quick preliminary analysis of this {prompt_type.value} prompt.
            
Identify obvious issues like:
- Missing critical information
- Unclear instructions
- Lack of specificity
            
Keep it brief and actionable."""
            
            user_prompt = f"Quick preliminary analysis of this prompt:\n\n{prompt}"
            
            response = grok_api.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=800  # Shorter for preliminary
            )
            
            return AgentOutput(
                success=True,
                content=response["content"],
                metadata={"preliminary": True, "tokens_used": response["usage"]["total_tokens"]}
            )
        except Exception as e:
            logger.error(f"Preliminary diagnosis error: {str(e)}")
            return AgentOutput(
                success=False,
                content="",
                errors=[str(e)]
            )
    
    def _extract_optimized_prompt(self, design_output: str) -> str:
        """Extract the optimized prompt text from designer output."""
        # Simple extraction - look for markers like "Optimized Prompt:" or code blocks
        lines = design_output.split('\n')
        in_prompt = False
        prompt_lines = []
        
        for line in lines:
            if any(marker in line.lower() for marker in ["optimized prompt", "improved prompt", "refined prompt"]):
                in_prompt = True
                continue
            if in_prompt:
                if line.strip().startswith('#') or line.strip().startswith('```'):
                    if prompt_lines:  # If we already started collecting, stop
                        break
                    continue
                if line.strip():
                    prompt_lines.append(line)
                    # Stop if we hit explanation section
                    if any(marker in line.lower() for marker in ["explanation", "improvements", "key changes"]):
                        break
        
        if prompt_lines:
            return '\n'.join(prompt_lines).strip()
        
        # Fallback: return first substantial paragraph
        paragraphs = [p.strip() for p in design_output.split('\n\n') if len(p.strip()) > 50]
        return paragraphs[0] if paragraphs else design_output[:500]
