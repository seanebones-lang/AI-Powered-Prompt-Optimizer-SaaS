"""
Monitoring dashboard page for system health and cost tracking.
"""

import streamlit as st
import logging
import tempfile
from datetime import datetime

from cost_tracker import get_cost_optimizer
from circuit_breaker import get_api_circuit_breaker
from monitoring import get_metrics

logger = logging.getLogger(__name__)


def _show_cost_section() -> None:
    """Display cost tracking section."""
    st.markdown("### Cost Tracking")

    cost_optimizer = get_cost_optimizer()

    col1, col2, col3, col4 = st.columns(4)

    today_cost = cost_optimizer.get_today_cost()
    month_cost = cost_optimizer.get_month_cost()

    with col1:
        st.metric("Today's Cost", f"${today_cost:.2f}")
    with col2:
        st.metric("This Month", f"${month_cost:.2f}")
    with col3:
        forecast = cost_optimizer.get_forecast(30)
        st.metric("30-Day Forecast", f"${forecast.get('estimated_cost', 0):.2f}")
    with col4:
        summary = cost_optimizer.get_summary()
        st.metric("Total Calls", summary.get('total_calls', 0))

    # Budget management
    with st.expander("Budget Management"):
        col1, col2 = st.columns(2)
        with col1:
            daily_budget = st.number_input(
                "Daily Budget ($)",
                min_value=0.0,
                value=10.0,
                step=1.0
            )
        with col2:
            monthly_budget = st.number_input(
                "Monthly Budget ($)",
                min_value=0.0,
                value=100.0,
                step=10.0
            )

        if st.button("Set Budgets"):
            cost_optimizer.set_budgets(daily=daily_budget, monthly=monthly_budget)
            st.success("Budgets updated!")


def _show_cost_breakdown() -> None:
    """Display detailed cost breakdown."""
    st.markdown("### Cost Breakdown")

    cost_optimizer = get_cost_optimizer()
    summary = cost_optimizer.get_summary()

    tab1, tab2, tab3 = st.tabs(["By Model", "By Operation", "Recent Calls"])

    with tab1:
        if summary.get('by_model'):
            import pandas as pd
            model_data = []
            for model, stats in summary['by_model'].items():
                model_data.append({
                    "Model": model,
                    "Calls": stats.get('calls', 0),
                    "Total Cost": f"${stats.get('cost', 0):.4f}",
                    "Tokens": f"{stats.get('tokens', 0):,}"
                })
            df = pd.DataFrame(model_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No cost data yet")

    with tab2:
        if summary.get('by_operation'):
            import pandas as pd
            op_data = []
            for operation, stats in summary['by_operation'].items():
                op_data.append({
                    "Operation": operation,
                    "Calls": stats.get('calls', 0),
                    "Total Cost": f"${stats.get('cost', 0):.4f}",
                    "Tokens": f"{stats.get('tokens', 0):,}"
                })
            df = pd.DataFrame(op_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No cost data yet")

    with tab3:
        recent_records = cost_optimizer.records[-20:]
        if recent_records:
            import pandas as pd
            recent_data = []
            for record in reversed(recent_records):
                recent_data.append({
                    "Time": record.timestamp.strftime("%H:%M:%S"),
                    "Model": record.model,
                    "Operation": record.operation,
                    "Tokens": f"{record.total_tokens:,}",
                    "Cost": f"${record.cost_usd:.4f}"
                })
            df = pd.DataFrame(recent_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent calls")

    # Export button
    if st.button("Export Cost Data"):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            cost_optimizer.export_records(f.name)
            with open(f.name, 'r') as rf:
                data = rf.read()
            st.download_button(
                "Download JSON",
                data=data,
                file_name=f"cost_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def _show_health_section() -> None:
    """Display system health section."""
    st.markdown("### System Health")

    circuit_breaker = get_api_circuit_breaker()
    metrics = get_metrics()

    col1, col2, col3 = st.columns(3)

    circuit_state = circuit_breaker.get_state()

    with col1:
        if circuit_state.value == "closed":
            st.success("API Circuit: HEALTHY")
        elif circuit_state.value == "half_open":
            st.warning("API Circuit: TESTING")
        else:
            st.error("API Circuit: DEGRADED")

    with col2:
        st.metric("API Calls", metrics.get_counter('api_requests'))

    with col3:
        cache_hits = metrics.get_counter('api_cache_hits')
        total_requests = metrics.get_counter('api_requests')
        cache_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        st.metric("Cache Hit Rate", f"{cache_rate:.1f}%")


def _show_performance_section() -> None:
    """Display performance metrics section."""
    st.markdown("### Performance Metrics")

    metrics = get_metrics()
    timer_stats = metrics.get_timer_stats('api_request')

    if timer_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Latency", f"{timer_stats.get('avg', 0)*1000:.0f}ms")
        with col2:
            st.metric("P95 Latency", f"{timer_stats.get('p95', 0)*1000:.0f}ms")
        with col3:
            st.metric("Min Latency", f"{timer_stats.get('min', 0)*1000:.0f}ms")
        with col4:
            st.metric("Max Latency", f"{timer_stats.get('max', 0)*1000:.0f}ms")
    else:
        st.info("No performance data available yet")

    # System controls
    with st.expander("System Controls"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Circuit Breaker"):
                circuit_breaker = get_api_circuit_breaker()
                circuit_breaker.reset()
                st.success("Circuit breaker reset!")
        with col2:
            if st.button("Clear Metrics"):
                metrics = get_metrics()
                metrics.reset()
                st.success("Metrics cleared!")


def show_monitoring_page() -> None:
    """Display the monitoring dashboard page."""
    st.markdown('<h2>Monitoring & Cost Dashboard</h2>', unsafe_allow_html=True)

    _show_cost_section()

    st.markdown("---")

    _show_cost_breakdown()

    st.markdown("---")

    _show_health_section()

    st.markdown("---")

    _show_performance_section()
