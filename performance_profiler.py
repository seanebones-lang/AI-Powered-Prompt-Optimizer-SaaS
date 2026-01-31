"""
Performance Profiler
Tracks and analyzes performance metrics for prompts and agents.

Features:
- Latency breakdown by component
- Token usage tracking
- Cost analysis
- Performance regression detection
- Optimization suggestions
- Bottleneck identification
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tokens_used: Dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self):
        """Mark metric as finished and calculate duration."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time


@dataclass
class ProfileResult:
    """Result of a performance profiling session."""
    total_duration: float
    metrics: List[PerformanceMetric]
    breakdown: Dict[str, float]
    total_tokens: int
    total_cost: float
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str


class PerformanceProfiler:
    """Profiles performance of prompt operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: List[PerformanceMetric] = []
        self.session_start: Optional[float] = None
        self.active_metric: Optional[PerformanceMetric] = None

    def start_session(self):
        """Start a new profiling session."""
        self.metrics = []
        self.session_start = time.time()
        self.logger.info("Started performance profiling session")

    def start_metric(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetric:
        """Start tracking a new metric."""
        metric = PerformanceMetric(
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.active_metric = metric
        self.metrics.append(metric)
        return metric

    def finish_metric(
        self,
        tokens_used: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None
    ):
        """Finish the active metric."""
        if self.active_metric:
            self.active_metric.finish()
            if tokens_used:
                self.active_metric.tokens_used = tokens_used
            if cost is not None:
                self.active_metric.cost = cost
            self.active_metric = None

    def end_session(self) -> ProfileResult:
        """End profiling session and generate results."""
        if self.session_start is None:
            raise ValueError("No active profiling session")

        total_duration = time.time() - self.session_start

        # Calculate breakdown by component
        breakdown = {}
        for metric in self.metrics:
            if metric.duration:
                breakdown[metric.name] = breakdown.get(metric.name, 0) + metric.duration

        # Calculate totals
        total_tokens = sum(
            sum(m.tokens_used.values()) for m in self.metrics
        )
        total_cost = sum(m.cost for m in self.metrics)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(self.metrics, total_duration)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            self.metrics,
            breakdown,
            bottlenecks
        )

        result = ProfileResult(
            total_duration=total_duration,
            metrics=self.metrics,
            breakdown=breakdown,
            total_tokens=total_tokens,
            total_cost=total_cost,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )

        # Reset session
        self.session_start = None

        return result

    def _identify_bottlenecks(
        self,
        metrics: List[PerformanceMetric],
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []

        # Sort metrics by duration
        sorted_metrics = sorted(
            [m for m in metrics if m.duration],
            key=lambda x: x.duration,
            reverse=True
        )

        for metric in sorted_metrics[:5]:  # Top 5 slowest
            percentage = (metric.duration / total_duration) * 100

            if percentage > 20:  # If taking more than 20% of total time
                bottlenecks.append({
                    "component": metric.name,
                    "duration": metric.duration,
                    "percentage": percentage,
                    "severity": "high" if percentage > 40 else "medium",
                    "tokens": sum(metric.tokens_used.values()),
                    "cost": metric.cost
                })

        return bottlenecks

    def _generate_recommendations(
        self,
        metrics: List[PerformanceMetric],
        breakdown: Dict[str, float],
        bottlenecks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Analyze bottlenecks
        for bottleneck in bottlenecks:
            component = bottleneck["component"]

            if "api" in component.lower() or "call" in component.lower():
                recommendations.append(
                    f"⚡ Optimize {component}: Consider caching, reducing token count, or using a faster model"
                )

            if bottleneck["tokens"] > 10000:
                recommendations.append(
                    f"📊 {component} uses {bottleneck['tokens']} tokens - consider compression or summarization"
                )

        # Check for sequential operations that could be parallelized
        if len(metrics) > 3:
            sequential_time = sum(m.duration for m in metrics if m.duration)
            if sequential_time > 10:  # More than 10 seconds
                recommendations.append(
                    "🔄 Consider parallelizing independent operations to reduce total time"
                )

        # Cost optimization
        total_cost = sum(m.cost for m in metrics)
        if total_cost > 0.10:  # More than 10 cents per operation
            recommendations.append(
                f"💰 High cost per operation (${total_cost:.4f}) - consider using cheaper models for non-critical components"
            )

        # Token efficiency
        total_tokens = sum(sum(m.tokens_used.values()) for m in metrics)
        if total_tokens > 50000:
            recommendations.append(
                f"📝 High token usage ({total_tokens}) - implement token budget management"
            )

        return recommendations

    def profile_function(self, name: Optional[str] = None):
        """Decorator to profile a function."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                metric_name = name or func.__name__
                self.start_metric(metric_name)

                try:
                    result = func(*args, **kwargs)
                    self.finish_metric()
                    return result
                except Exception as e:
                    self.finish_metric()
                    raise e

            return wrapper
        return decorator

    def compare_profiles(
        self,
        baseline: ProfileResult,
        current: ProfileResult
    ) -> Dict[str, Any]:
        """Compare two profile results to detect regressions."""
        comparison = {
            "duration_change": {
                "baseline": baseline.total_duration,
                "current": current.total_duration,
                "delta": current.total_duration - baseline.total_duration,
                "percentage": ((current.total_duration - baseline.total_duration) / baseline.total_duration) * 100
            },
            "cost_change": {
                "baseline": baseline.total_cost,
                "current": current.total_cost,
                "delta": current.total_cost - baseline.total_cost,
                "percentage": ((current.total_cost - baseline.total_cost) / baseline.total_cost) * 100 if baseline.total_cost > 0 else 0
            },
            "token_change": {
                "baseline": baseline.total_tokens,
                "current": current.total_tokens,
                "delta": current.total_tokens - baseline.total_tokens,
                "percentage": ((current.total_tokens - baseline.total_tokens) / baseline.total_tokens) * 100 if baseline.total_tokens > 0 else 0
            },
            "regressions": [],
            "improvements": []
        }

        # Check for regressions
        if comparison["duration_change"]["percentage"] > 10:
            comparison["regressions"].append(
                f"⚠️ Performance regression: {comparison['duration_change']['percentage']:.1f}% slower"
            )

        if comparison["cost_change"]["percentage"] > 10:
            comparison["regressions"].append(
                f"⚠️ Cost regression: {comparison['cost_change']['percentage']:.1f}% more expensive"
            )

        # Check for improvements
        if comparison["duration_change"]["percentage"] < -10:
            comparison["improvements"].append(
                f"✅ Performance improvement: {abs(comparison['duration_change']['percentage']):.1f}% faster"
            )

        if comparison["cost_change"]["percentage"] < -10:
            comparison["improvements"].append(
                f"✅ Cost improvement: {abs(comparison['cost_change']['percentage']):.1f}% cheaper"
            )

        return comparison


class CostTracker:
    """Track costs across operations."""

    # Pricing per 1K tokens (as of 2026)
    MODEL_PRICING = {
        "grok-beta": {"input": 0.15, "output": 0.60},
        "grok-2": {"input": 0.10, "output": 0.40},
        "claude-opus": {"input": 15.00, "output": 75.00},
        "claude-sonnet": {"input": 3.00, "output": 15.00},
        "claude-haiku": {"input": 0.80, "output": 4.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self):
        self.operations: List[Dict[str, Any]] = []

    def track_operation(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation_type: str = "optimization",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a single operation's cost."""
        pricing = self.MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})

        cost = (
            (input_tokens / 1000 * pricing["input"]) +
            (output_tokens / 1000 * pricing["output"])
        )

        operation = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "operation_type": operation_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "metadata": metadata or {}
        }

        self.operations.append(operation)

    def get_summary(
        self,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cost summary."""
        if not self.operations:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "operation_count": 0
            }

        # Filter by time period if specified
        operations = self.operations  # TODO: Implement time filtering

        total_cost = sum(op["cost"] for op in operations)
        total_tokens = sum(op["total_tokens"] for op in operations)

        # Group by model
        by_model = {}
        for op in operations:
            model = op["model"]
            if model not in by_model:
                by_model[model] = {
                    "operations": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            by_model[model]["operations"] += 1
            by_model[model]["tokens"] += op["total_tokens"]
            by_model[model]["cost"] += op["cost"]

        # Group by operation type
        by_type = {}
        for op in operations:
            op_type = op["operation_type"]
            if op_type not in by_type:
                by_type[op_type] = {
                    "operations": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            by_type[op_type]["operations"] += 1
            by_type[op_type]["tokens"] += op["total_tokens"]
            by_type[op_type]["cost"] += op["cost"]

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "operation_count": len(operations),
            "average_cost_per_operation": total_cost / len(operations),
            "by_model": by_model,
            "by_type": by_type,
            "most_expensive_model": max(by_model.items(), key=lambda x: x[1]["cost"])[0] if by_model else None,
            "most_used_model": max(by_model.items(), key=lambda x: x[1]["operations"])[0] if by_model else None
        }

    def project_costs(
        self,
        operations_per_day: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Project future costs based on current usage."""
        if not self.operations:
            return {"error": "No operations to base projection on"}

        avg_cost = sum(op["cost"] for op in self.operations) / len(self.operations)

        daily_cost = avg_cost * operations_per_day
        monthly_cost = daily_cost * days
        yearly_cost = daily_cost * 365

        return {
            "average_cost_per_operation": avg_cost,
            "projected_daily_cost": daily_cost,
            "projected_monthly_cost": monthly_cost,
            "projected_yearly_cost": yearly_cost,
            "operations_per_day": operations_per_day,
            "assumptions": f"Based on average of {len(self.operations)} operations"
        }

    def suggest_cost_optimizations(self) -> List[str]:
        """Suggest ways to reduce costs."""
        if not self.operations:
            return []

        suggestions = []
        summary = self.get_summary()

        # Check if using expensive models
        if summary.get("most_expensive_model") in ["claude-opus", "gpt-4"]:
            suggestions.append(
                "💰 Consider using cheaper models like Claude Sonnet or GPT-3.5 for non-critical operations"
            )

        # Check average tokens per operation
        avg_tokens = summary["total_tokens"] / summary["operation_count"]
        if avg_tokens > 10000:
            suggestions.append(
                f"📊 High average token usage ({int(avg_tokens)}) - implement prompt compression"
            )

        # Check if costs are high
        if summary["total_cost"] > 10.0:
            suggestions.append(
                "⚠️ High cumulative costs - consider implementing caching and rate limiting"
            )

        # Model-specific suggestions
        by_model = summary.get("by_model", {})
        for model, stats in by_model.items():
            if stats["cost"] > summary["total_cost"] * 0.5:  # More than 50% of costs
                suggestions.append(
                    f"🎯 {model} accounts for {(stats['cost']/summary['total_cost']*100):.0f}% of costs - optimize or switch models"
                )

        return suggestions

    def export_report(self, format: str = "json") -> str:
        """Export cost report."""
        summary = self.get_summary()

        if format == "json":
            return json.dumps(summary, indent=2)
        elif format == "markdown":
            return f"""# Cost Report

## Summary
- **Total Cost:** ${summary['total_cost']:.4f}
- **Total Tokens:** {summary['total_tokens']:,}
- **Operations:** {summary['operation_count']}
- **Average Cost/Op:** ${summary['average_cost_per_operation']:.4f}

## By Model
{chr(10).join(f"- **{model}:** ${stats['cost']:.4f} ({stats['operations']} ops, {stats['tokens']:,} tokens)" for model, stats in summary.get('by_model', {}).items())}

## By Operation Type
{chr(10).join(f"- **{op_type}:** ${stats['cost']:.4f} ({stats['operations']} ops)" for op_type, stats in summary.get('by_type', {}).items())}

## Recommendations
{chr(10).join(f"- {suggestion}" for suggestion in self.suggest_cost_optimizations())}
"""
        else:
            return str(summary)


# Global instances
_profiler = PerformanceProfiler()
_cost_tracker = CostTracker()


# Convenience functions
def start_profiling():
    """Start a profiling session."""
    _profiler.start_session()


def stop_profiling() -> ProfileResult:
    """Stop profiling and get results."""
    return _profiler.end_session()


def track_cost(model: str, input_tokens: int, output_tokens: int, **kwargs):
    """Track operation cost."""
    _cost_tracker.track_operation(model, input_tokens, output_tokens, **kwargs)


def get_cost_summary() -> Dict[str, Any]:
    """Get cost summary."""
    return _cost_tracker.get_summary()


def profile(name: Optional[str] = None):
    """Decorator to profile a function."""
    return _profiler.profile_function(name)
