"""
Streamlit page modules for the Prompt Optimizer.

This package contains individual page modules:
- optimize: Main prompt optimization page
- batch: Batch optimization processing
- analytics: Analytics dashboard
- ab_testing: A/B testing interface
- enterprise: Enterprise features
- history: Session history
- settings_page: Settings and preferences
- monitoring: System monitoring

Usage:
    from pages import PAGE_REGISTRY

    # Get page function by name
    page_func = PAGE_REGISTRY.get("optimize")
    page_func()
"""

from pages.optimize import show_optimize_page
from pages.batch import show_batch_page
from pages.analytics import show_analytics_page
from pages.ab_testing import show_ab_testing_page
from pages.enterprise import show_enterprise_page
from pages.history import show_history_page
from pages.settings_page import show_settings_page
from pages.monitoring import show_monitoring_page

# Page registry for dynamic page loading
PAGE_REGISTRY = {
    "optimize": show_optimize_page,
    "batch": show_batch_page,
    "analytics": show_analytics_page,
    "ab_testing": show_ab_testing_page,
    "enterprise": show_enterprise_page,
    "history": show_history_page,
    "settings": show_settings_page,
    "monitoring": show_monitoring_page,
}

# Navigation labels for sidebar
PAGE_LABELS = {
    "optimize": "Optimize",
    "batch": "Batch",
    "analytics": "Analytics",
    "ab_testing": "A/B Testing",
    "enterprise": "Enterprise",
    "history": "History",
    "settings": "Settings",
    "monitoring": "Monitoring",
}

__all__ = [
    "PAGE_REGISTRY",
    "PAGE_LABELS",
    "show_optimize_page",
    "show_batch_page",
    "show_analytics_page",
    "show_ab_testing_page",
    "show_enterprise_page",
    "show_history_page",
    "show_settings_page",
    "show_monitoring_page",
]
