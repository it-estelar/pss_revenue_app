"""
Core app-shell exports.

This package contains the public helpers used by app.py to run the
application shell: styles, branding, layout, navigation, and module dispatch.
"""

from .branding import render_sidebar_logo
from .layout import build_report_period, safe_unique_sorted, show_header, show_kpis
from .module_registry import get_module_registry, get_module_runner
from .navigation import (
    MODULES_BY_ROLE,
    get_module_labels_for_role,
    render_sidebar_navigation,
)
from .styles import apply_app_styles

__all__ = [
    "apply_app_styles",
    "render_sidebar_logo",
    "build_report_period",
    "safe_unique_sorted",
    "show_header",
    "show_kpis",
    "MODULES_BY_ROLE",
    "get_module_labels_for_role",
    "render_sidebar_navigation",
    "get_module_registry",
    "get_module_runner",
]