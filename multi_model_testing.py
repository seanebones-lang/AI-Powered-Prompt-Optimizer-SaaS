"""
Multi-Model Testing Framework
Test prompts across multiple AI models (Grok, Claude, GPT-4, Gemini, Llama).

Features:
- Side-by-side model comparison
- Performance benchmarking
- Cost analysis
- Quality scoring
- Model recommendations
- A/B testing across models
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Supported AI models."""
    GROK_BETA = "grok-beta"
    GROK_2 = "grok-2-1212"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    LLAMA_70B = "llama-2-70b"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model: AIModel
    api_key: str
    api_base: str
    temperature: float = 0.7
    max_tokens: int = 4000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class ModelResponse:
    """Response from a model."""
    model: AIModel
    content: str
    latency: float  # seconds
    tokens_used: Dict[str, int]  # input, output, total
    cost: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ComparisonResult:
    """Result of comparing multiple models."""
    prompt: str
    responses: List[ModelResponse]
    winner: Optional[AIModel]
    comparison_matrix: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


class MultiModelTester:
    """Test prompts across multiple AI models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_configs: Dict[AIModel, ModelConfig] = {}
        self._init_default_configs()

    def _init_default_configs(self):
        """Initialize default model configurations."""
        # Note: Users need to provide their own API keys
        import os

        # Grok models
        xai_key = os.getenv("XAI_API_KEY", "")
        if xai_key:
            self.model_configs[AIModel.GROK_BETA] = ModelConfig(
                model=AIModel.GROK_BETA,
                api_key=xai_key,
                api_base="https://api.x.ai/v1",
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.60
            )
            self.model_configs[AIModel.GROK_2] = ModelConfig(
                model=AIModel.GROK_2,
                api_key=xai_key,
                api_base="https://api.x.ai/v1",
                cost_per_1k_input=0.10,
                cost_per_1k_output=0.40
            )

        # Claude models
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        if claude_key:
            self.model_configs[AIModel.CLAUDE_OPUS] = ModelConfig(
                model=AIModel.CLAUDE_OPUS,
                api_key=claude_key,
                api_base="https://api.anthropic.com/v1",
                cost_per_1k_input=15.00,
                cost_per_1k_output=75.00
            )
            self.model_configs[AIModel.CLAUDE_SONNET] = ModelConfig(
                model=AIModel.CLAUDE_SONNET,
                api_key=claude_key,
                api_base="https://api.anthropic.com/v1",
                cost_per_1k_input=3.00,
                cost_per_1k_output=15.00
            )
            self.model_configs[AIModel.CLAUDE_HAIKU] = ModelConfig(
                model=AIModel.CLAUDE_HAIKU,
                api_key=claude_key,
                api_base="https://api.anthropic.com/v1",
                cost_per_1k_input=0.80,
                cost_per_1k_output=4.00
            )

        # OpenAI models
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            self.model_configs[AIModel.GPT4_TURBO] = ModelConfig(
                model=AIModel.GPT4_TURBO,
                api_key=openai_key,
                api_base="https://api.openai.com/v1",
                cost_per_1k_input=10.00,
                cost_per_1k_output=30.00
            )
            self.model_configs[AIModel.GPT4] = ModelConfig(
                model=AIModel.GPT4,
                api_key=openai_key,
                api_base="https://api.openai.com/v1",
                cost_per_1k_input=30.00,
                cost_per_1k_output=60.00
            )
            self.model_configs[AIModel.GPT35_TURBO] = ModelConfig(
                model=AIModel.GPT35_TURBO,
                api_key=openai_key,
                api_base="https://api.openai.com/v1",
                cost_per_1k_input=0.50,
                cost_per_1k_output=1.50
            )

    def add_model_config(self, config: ModelConfig):
        """Add or update a model configuration."""
        self.model_configs[config.model] = config

    def test_prompt_across_models(
        self,
        prompt: str,
        models: List[AIModel],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ComparisonResult:
        """
        Test a prompt across multiple models.
        
        Args:
            prompt: The prompt to test
            models: List of models to test
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            
        Returns:
            ComparisonResult with responses from all models
        """
        self.logger.info(f"Testing prompt across {len(models)} models")

        responses = []

        for model in models:
            if model not in self.model_configs:
                self.logger.warning(f"Model {model.value} not configured, skipping")
                continue

            try:
                response = self._call_model(
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Error testing {model.value}: {str(e)}")
                responses.append(ModelResponse(
                    model=model,
                    content="",
                    latency=0.0,
                    tokens_used={"input": 0, "output": 0, "total": 0},
                    cost=0.0,
                    error=str(e)
                ))

        # Analyze results
        comparison_matrix = self._build_comparison_matrix(responses)
        winner = self._determine_winner(responses, comparison_matrix)
        recommendations = self._generate_recommendations(responses, comparison_matrix)

        return ComparisonResult(
            prompt=prompt,
            responses=responses,
            winner=winner,
            comparison_matrix=comparison_matrix,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )

    def _call_model(
        self,
        model: AIModel,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ModelResponse:
        """Call a specific model API."""
        config = self.model_configs[model]

        # Override config if specified
        temp = temperature if temperature is not None else config.temperature
        tokens = max_tokens if max_tokens is not None else config.max_tokens

        start_time = time.time()

        try:
            if model.value.startswith("grok"):
                response = self._call_grok(config, prompt, system_prompt, temp, tokens)
            elif model.value.startswith("claude"):
                response = self._call_claude(config, prompt, system_prompt, temp, tokens)
            elif model.value.startswith("gpt"):
                response = self._call_openai(config, prompt, system_prompt, temp, tokens)
            elif model.value.startswith("gemini"):
                response = self._call_gemini(config, prompt, system_prompt, temp, tokens)
            else:
                raise ValueError(f"Unsupported model: {model.value}")

            latency = time.time() - start_time

            # Calculate cost
            input_tokens = response["tokens_used"]["input"]
            output_tokens = response["tokens_used"]["output"]
            cost = (
                (input_tokens / 1000 * config.cost_per_1k_input) +
                (output_tokens / 1000 * config.cost_per_1k_output)
            )

            return ModelResponse(
                model=model,
                content=response["content"],
                latency=latency,
                tokens_used=response["tokens_used"],
                cost=cost,
                metadata=response.get("metadata", {})
            )
        except Exception as e:
            latency = time.time() - start_time
            raise Exception(f"Error calling {model.value}: {str(e)}")

    def _call_grok(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call Grok API."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": config.model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{config.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

        return {
            "content": result["choices"][0]["message"]["content"],
            "tokens_used": {
                "input": result["usage"]["prompt_tokens"],
                "output": result["usage"]["completion_tokens"],
                "total": result["usage"]["total_tokens"]
            }
        }

    def _call_claude(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call Claude API."""
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        data = {
            "model": config.model.value,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if system_prompt:
            data["system"] = system_prompt

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{config.api_base}/messages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

        return {
            "content": result["content"][0]["text"],
            "tokens_used": {
                "input": result["usage"]["input_tokens"],
                "output": result["usage"]["output_tokens"],
                "total": result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
            }
        }

    def _call_openai(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call OpenAI API."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": config.model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{config.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

        return {
            "content": result["choices"][0]["message"]["content"],
            "tokens_used": {
                "input": result["usage"]["prompt_tokens"],
                "output": result["usage"]["completion_tokens"],
                "total": result["usage"]["total_tokens"]
            }
        }

    def _call_gemini(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call Gemini API."""
        # Gemini API implementation
        # Note: This is a simplified version
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"https://generativelanguage.googleapis.com/v1/models/{config.model.value}:generateContent?key={config.api_key}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

        content = result["candidates"][0]["content"]["parts"][0]["text"]

        # Estimate tokens (Gemini doesn't always provide exact counts)
        input_tokens = len(full_prompt.split()) * 1.3  # Rough estimate
        output_tokens = len(content.split()) * 1.3

        return {
            "content": content,
            "tokens_used": {
                "input": int(input_tokens),
                "output": int(output_tokens),
                "total": int(input_tokens + output_tokens)
            }
        }

    def _build_comparison_matrix(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Build a comparison matrix of model performance."""
        if not responses:
            return {}

        # Filter out errors
        valid_responses = [r for r in responses if not r.error]

        if not valid_responses:
            return {"error": "All models failed"}

        return {
            "latency": {
                "fastest": min(valid_responses, key=lambda r: r.latency),
                "slowest": max(valid_responses, key=lambda r: r.latency),
                "average": sum(r.latency for r in valid_responses) / len(valid_responses)
            },
            "cost": {
                "cheapest": min(valid_responses, key=lambda r: r.cost),
                "most_expensive": max(valid_responses, key=lambda r: r.cost),
                "total": sum(r.cost for r in valid_responses),
                "average": sum(r.cost for r in valid_responses) / len(valid_responses)
            },
            "tokens": {
                "most_efficient": min(valid_responses, key=lambda r: r.tokens_used["total"]),
                "least_efficient": max(valid_responses, key=lambda r: r.tokens_used["total"]),
                "average": sum(r.tokens_used["total"] for r in valid_responses) / len(valid_responses)
            },
            "output_length": {
                "longest": max(valid_responses, key=lambda r: len(r.content)),
                "shortest": min(valid_responses, key=lambda r: len(r.content)),
                "average": sum(len(r.content) for r in valid_responses) / len(valid_responses)
            }
        }

    def _determine_winner(
        self,
        responses: List[ModelResponse],
        comparison_matrix: Dict[str, Any]
    ) -> Optional[AIModel]:
        """Determine the best model based on multiple factors."""
        valid_responses = [r for r in responses if not r.error]

        if not valid_responses:
            return None

        # Score each model
        scores = {}

        for response in valid_responses:
            score = 0

            # Speed (30% weight)
            if response.latency == comparison_matrix["latency"]["fastest"].latency:
                score += 30
            else:
                # Proportional score
                fastest = comparison_matrix["latency"]["fastest"].latency
                score += 30 * (fastest / response.latency)

            # Cost (30% weight)
            if response.cost == comparison_matrix["cost"]["cheapest"].cost:
                score += 30
            else:
                cheapest = comparison_matrix["cost"]["cheapest"].cost
                score += 30 * (cheapest / response.cost) if response.cost > 0 else 30

            # Output quality (40% weight) - based on length and completeness
            # Longer outputs generally indicate more detail
            if len(response.content) == len(comparison_matrix["output_length"]["longest"].content):
                score += 40
            else:
                longest = len(comparison_matrix["output_length"]["longest"].content)
                score += 40 * (len(response.content) / longest) if longest > 0 else 20

            scores[response.model] = score

        # Return model with highest score
        winner = max(scores.items(), key=lambda x: x[1])
        return winner[0]

    def _generate_recommendations(
        self,
        responses: List[ModelResponse],
        comparison_matrix: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []

        valid_responses = [r for r in responses if not r.error]

        if not valid_responses:
            return ["All models failed. Check API keys and connectivity."]

        # Speed recommendation
        fastest = comparison_matrix["latency"]["fastest"]
        recommendations.append(
            f"🚀 Fastest: {fastest.model.value} ({fastest.latency:.2f}s)"
        )

        # Cost recommendation
        cheapest = comparison_matrix["cost"]["cheapest"]
        recommendations.append(
            f"💰 Most Cost-Effective: {cheapest.model.value} (${cheapest.cost:.4f})"
        )

        # Quality recommendation (based on output length as proxy)
        longest = comparison_matrix["output_length"]["longest"]
        recommendations.append(
            f"📝 Most Detailed: {longest.model.value} ({len(longest.content)} chars)"
        )

        # Overall recommendation
        if comparison_matrix.get("latency") and comparison_matrix.get("cost"):
            avg_latency = comparison_matrix["latency"]["average"]
            avg_cost = comparison_matrix["cost"]["average"]

            # Find balanced model (good speed and cost)
            balanced = min(
                valid_responses,
                key=lambda r: (
                    abs(r.latency - avg_latency) / avg_latency +
                    abs(r.cost - avg_cost) / avg_cost if avg_cost > 0 else 0
                )
            )
            recommendations.append(
                f"⚖️ Best Balance: {balanced.model.value}"
            )

        return recommendations

    def benchmark_models(
        self,
        test_prompts: List[str],
        models: List[AIModel],
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Benchmark models across multiple prompts and iterations.
        
        Args:
            test_prompts: List of prompts to test
            models: Models to benchmark
            iterations: Number of iterations per prompt
            
        Returns:
            Comprehensive benchmark results
        """
        self.logger.info(f"Benchmarking {len(models)} models with {len(test_prompts)} prompts, {iterations} iterations each")

        results = {
            "models": [m.value for m in models],
            "prompts_tested": len(test_prompts),
            "iterations": iterations,
            "total_tests": len(test_prompts) * len(models) * iterations,
            "model_stats": {},
            "detailed_results": []
        }

        # Initialize stats for each model
        for model in models:
            results["model_stats"][model.value] = {
                "total_latency": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_latency": 0.0,
                "avg_cost": 0.0,
                "avg_tokens": 0
            }

        # Run tests
        for prompt_idx, prompt in enumerate(test_prompts):
            for iteration in range(iterations):
                self.logger.info(f"Testing prompt {prompt_idx + 1}/{len(test_prompts)}, iteration {iteration + 1}/{iterations}")

                comparison = self.test_prompt_across_models(
                    prompt=prompt,
                    models=models
                )

                results["detailed_results"].append({
                    "prompt_index": prompt_idx,
                    "iteration": iteration,
                    "comparison": comparison
                })

                # Update stats
                for response in comparison.responses:
                    stats = results["model_stats"][response.model.value]

                    if response.error:
                        stats["error_count"] += 1
                    else:
                        stats["success_count"] += 1
                        stats["total_latency"] += response.latency
                        stats["total_cost"] += response.cost
                        stats["total_tokens"] += response.tokens_used["total"]

        # Calculate averages
        for model_name, stats in results["model_stats"].items():
            if stats["success_count"] > 0:
                stats["avg_latency"] = stats["total_latency"] / stats["success_count"]
                stats["avg_cost"] = stats["total_cost"] / stats["success_count"]
                stats["avg_tokens"] = stats["total_tokens"] / stats["success_count"]

        # Generate summary
        results["summary"] = self._generate_benchmark_summary(results)

        return results

    def _generate_benchmark_summary(self, results: Dict[str, Any]) -> str:
        """Generate a summary of benchmark results."""
        summary_parts = [
            "Benchmark Results:",
            f"Total Tests: {results['total_tests']}",
            f"Models Tested: {len(results['models'])}",
            ""
        ]

        # Sort models by average latency
        sorted_by_speed = sorted(
            results["model_stats"].items(),
            key=lambda x: x[1]["avg_latency"] if x[1]["success_count"] > 0 else float('inf')
        )

        summary_parts.append("Speed Rankings:")
        for rank, (model, stats) in enumerate(sorted_by_speed, 1):
            if stats["success_count"] > 0:
                summary_parts.append(
                    f"{rank}. {model}: {stats['avg_latency']:.2f}s avg"
                )

        summary_parts.append("")

        # Sort by cost
        sorted_by_cost = sorted(
            results["model_stats"].items(),
            key=lambda x: x[1]["avg_cost"] if x[1]["success_count"] > 0 else float('inf')
        )

        summary_parts.append("Cost Rankings:")
        for rank, (model, stats) in enumerate(sorted_by_cost, 1):
            if stats["success_count"] > 0:
                summary_parts.append(
                    f"{rank}. {model}: ${stats['avg_cost']:.4f} avg"
                )

        return "\n".join(summary_parts)


# Convenience function
def compare_models(
    prompt: str,
    models: Optional[List[str]] = None,
    **kwargs
) -> ComparisonResult:
    """
    Convenience function to compare models.
    
    Args:
        prompt: Prompt to test
        models: List of model names (strings)
        **kwargs: Additional options
        
    Returns:
        ComparisonResult
    """
    tester = MultiModelTester()

    # Convert string model names to enums
    if models is None:
        # Default to available models
        model_enums = [m for m in AIModel if m in tester.model_configs]
    else:
        model_enums = [AIModel(m) for m in models]

    return tester.test_prompt_across_models(
        prompt=prompt,
        models=model_enums,
        system_prompt=kwargs.get('system_prompt'),
        temperature=kwargs.get('temperature'),
        max_tokens=kwargs.get('max_tokens')
    )
