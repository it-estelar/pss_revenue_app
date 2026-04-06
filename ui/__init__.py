"""
Public UI-layer exports.

This package exposes the Streamlit render functions and shared UI helpers used
by the module router. Keep rendering concerns here; avoid moving business
aggregation logic into this package.
"""

# -----------------------------------------------------------------------------
# Shared UI helpers
# -----------------------------------------------------------------------------

from .export_controls import build_pdf_subtitle, render_export_buttons
from .filters import render_module_date_filters
from .formatters import metric_text_int, metric_text_money

# -----------------------------------------------------------------------------
# Module views
# -----------------------------------------------------------------------------

from .admin_view import render_admin_panel
from .dashboard_view import render_dashboard
from .emisor_view import render_revenue_by_emisor
from .load_view import render_data_load_module
from .matrix_view import render_route_matrix
from .programmed_revenue_view import render_programmed_revenue_module
from .route_view import render_route_analysis
from .sales_view import render_sales_module
from .tariff_view import render_tariff_style
from .user_sales_view import render_sales_by_user
from .volado_view import render_volado_module
from .yield_view import render_yield_by_route

__all__ = [
    # Shared UI helpers
    "build_pdf_subtitle",
    "render_export_buttons",
    "render_module_date_filters",
    "metric_text_int",
    "metric_text_money",

    # Module views
    "render_admin_panel",
    "render_dashboard",
    "render_revenue_by_emisor",
    "render_data_load_module",
    "render_route_matrix",
    "render_programmed_revenue_module",
    "render_route_analysis",
    "render_sales_module",
    "render_tariff_style",
    "render_sales_by_user",
    "render_volado_module",
    "render_yield_by_route",
]