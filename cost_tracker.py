"""
Cost tracking and optimization for API usage.
Helps minimize expenses while maintaining quality.
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


# Updated pricing for January 2026 (per 1M tokens)
MODEL_PRICING = {
    "grok-4-1-fast-reasoning": {"input": 3.00, "output": 15.00, "quality": 0.95},
    "grok-4-1-fast": {"input": 2.00, "output": 10.00, "quality": 0.90},
    "grok-3": {"input": 5.00, "output": 15.00, "quality": 0.92},
    "grok-3-fast": {"input": 3.00, "output": 10.00, "quality": 0.88},
    "grok-2": {"input": 2.00, "output": 6.00, "quality": 0.80},
    "grok-vision": {"input": 5.00, "output": 15.00, "quality": 0.93},
}


@dataclass
class CostRecord:
    """Record of a single API call cost."""
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    operation: str  # e.g., "optimization", "refinement", "test_generation"
    prompt_type: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "operation": self.operation,
            "prompt_type": self.prompt_type
        }


class CostOptimizer:
    """
    Cost optimization engine for API usage.
    
    Features:
    - Track costs per operation
    - Suggest cheaper models when appropriate
    - Budget alerts
    - Cost forecasting
    """

    def __init__(self):
        """Initialize cost optimizer."""
        self.records: List[CostRecord] = []
        self.daily_budget: Optional[float] = None
        self.monthly_budget: Optional[float] = None

        logger.info("Cost optimizer initialized")

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for API call.
        
        Args:
            model: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            
        Returns:
            Cost in USD
        """
        pricing = MODEL_PRICING.get(model, {"input": 2.0, "output": 10.0})

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def record_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation: str,
        prompt_type: Optional[str] = None
    ) -> CostRecord:
        """
        Record a cost entry.
        
        Args:
            model: Model used
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            operation: Operation type
            prompt_type: Optional prompt type
            
        Returns:
            Cost record
        """
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        record = CostRecord(
            timestamp=datetime.now(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            operation=operation,
            prompt_type=prompt_type
        )

        self.records.append(record)

        # Check budget alerts
        self._check_budget_alerts()

        return record

    def suggest_model(
        self,
        prompt_length: int,
        quality_requirement: float = 0.85,
        max_cost_per_call: Optional[float] = None
    ) -> Tuple[str, Dict]:
        """
        Suggest optimal model based on requirements.
        
        Args:
            prompt_length: Estimated prompt length in tokens
            quality_requirement: Minimum quality score (0-1)
            max_cost_per_call: Maximum acceptable cost
            
        Returns:
            Tuple of (model_name, model_info)
        """
        # Estimate completion tokens (typically 2-3x prompt for optimizations)
        estimated_completion = prompt_length * 2.5

        # Filter models by quality
        suitable_models = {
            name: info for name, info in MODEL_PRICING.items()
            if info["quality"] >= quality_requirement
        }

        if not suitable_models:
            # Fall back to best quality model
            best_model = max(MODEL_PRICING.items(), key=lambda x: x[1]["quality"])
            logger.warning(f"No models meet quality requirement {quality_requirement}, "
                         f"using best: {best_model[0]}")
            return best_model[0], best_model[1]

        # Calculate cost for each suitable model
        model_costs = {}
        for name, info in suitable_models.items():
            cost = self.calculate_cost(name, prompt_length, int(estimated_completion))
            if max_cost_per_call is None or cost <= max_cost_per_call:
                model_costs[name] = (cost, info)

        if not model_costs:
            # No models within budget, return cheapest suitable
            cheapest = min(
                suitable_models.items(),
                key=lambda x: self.calculate_cost(x[0], prompt_length, int(estimated_completion))
            )
            logger.warning(f"No models within budget ${max_cost_per_call}, "
                         f"using cheapest suitable: {cheapest[0]}")
            return cheapest[0], cheapest[1]

        # Return cheapest model within constraints
        best_model = min(model_costs.items(), key=lambda x: x[1][0])
        logger.info(f"Suggested model: {best_model[0]} (estimated cost: ${best_model[1][0]:.4f})")

        return best_model[0], best_model[1][1]

    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get cost summary for date range.
        
        Args:
            start_date: Start date (default: beginning of time)
            end_date: End date (default: now)
            
        Returns:
            Summary dictionary
        """
        filtered_records = self.records

        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]
        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]

        if not filtered_records:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "total_calls": 0,
                "by_model": {},
                "by_operation": {},
                "avg_cost_per_call": 0.0
            }

        total_cost = sum(r.cost_usd for r in filtered_records)
        total_tokens = sum(r.total_tokens for r in filtered_records)

        # Group by model
        by_model = defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens": 0})
        for record in filtered_records:
            by_model[record.model]["calls"] += 1
            by_model[record.model]["cost"] += record.cost_usd
            by_model[record.model]["tokens"] += record.total_tokens

        # Group by operation
        by_operation = defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens": 0})
        for record in filtered_records:
            by_operation[record.operation]["calls"] += 1
            by_operation[record.operation]["cost"] += record.cost_usd
            by_operation[record.operation]["tokens"] += record.total_tokens

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": len(filtered_records),
            "by_model": dict(by_model),
            "by_operation": dict(by_operation),
            "avg_cost_per_call": round(total_cost / len(filtered_records), 4)
        }

    def get_today_cost(self) -> float:
        """Get total cost for today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        summary = self.get_summary(start_date=today_start)
        return summary["total_cost"]

    def get_month_cost(self) -> float:
        """Get total cost for current month."""
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        summary = self.get_summary(start_date=month_start)
        return summary["total_cost"]

    def set_budgets(self, daily: Optional[float] = None, monthly: Optional[float] = None):
        """Set cost budgets."""
        if daily is not None:
            self.daily_budget = daily
            logger.info(f"Daily budget set to ${daily:.2f}")
        if monthly is not None:
            self.monthly_budget = monthly
            logger.info(f"Monthly budget set to ${monthly:.2f}")

    def _check_budget_alerts(self):
        """Check if budgets are being approached or exceeded."""
        if self.daily_budget:
            today_cost = self.get_today_cost()
            if today_cost >= self.daily_budget:
                logger.warning(f"⚠️ Daily budget exceeded: ${today_cost:.2f} / ${self.daily_budget:.2f}")
            elif today_cost >= self.daily_budget * 0.8:
                logger.info(f"ℹ️ Approaching daily budget: ${today_cost:.2f} / ${self.daily_budget:.2f}")

        if self.monthly_budget:
            month_cost = self.get_month_cost()
            if month_cost >= self.monthly_budget:
                logger.warning(f"⚠️ Monthly budget exceeded: ${month_cost:.2f} / ${self.monthly_budget:.2f}")
            elif month_cost >= self.monthly_budget * 0.8:
                logger.info(f"ℹ️ Approaching monthly budget: ${month_cost:.2f} / ${self.monthly_budget:.2f}")

    def export_records(self, filepath: str):
        """Export cost records to JSON file."""
        data = [r.to_dict() for r in self.records]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported {len(data)} cost records to {filepath}")

    def get_forecast(self, days: int = 30) -> Dict:
        """
        Forecast costs based on recent usage.
        
        Args:
            days: Number of days to forecast
            
        Returns:
            Forecast dictionary
        """
        # Use last 7 days for trend
        week_ago = datetime.now() - timedelta(days=7)
        recent_summary = self.get_summary(start_date=week_ago)

        if recent_summary["total_calls"] == 0:
            return {
                "forecast_days": days,
                "estimated_cost": 0.0,
                "confidence": "low"
            }

        # Calculate daily average
        daily_avg = recent_summary["total_cost"] / 7

        # Forecast
        estimated_cost = daily_avg * days

        return {
            "forecast_days": days,
            "estimated_cost": round(estimated_cost, 2),
            "daily_average": round(daily_avg, 2),
            "confidence": "medium" if recent_summary["total_calls"] > 20 else "low"
        }


# Global cost optimizer instance
_global_cost_optimizer = CostOptimizer()


def get_cost_optimizer() -> CostOptimizer:
    """Get global cost optimizer."""
    return _global_cost_optimizer
