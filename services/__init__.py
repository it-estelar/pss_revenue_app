"""
Public service-layer exports.

This package exposes the service functions that orchestrate report builders,
module-specific preparation logic, and admin/catalog helpers for the UI layer.
Keep business orchestration here; avoid putting Streamlit rendering logic in
this package.
"""

# -----------------------------------------------------------------------------
# Auth services
# -----------------------------------------------------------------------------

from .auth_service import (
    authenticate_user,
    create_app_user,
    get_app_users,
    hash_password,
    reset_app_user_password,
    update_app_user,
    verify_password,
)

# -----------------------------------------------------------------------------
# Admin / catalog services
# -----------------------------------------------------------------------------

from .admin_service import (
    change_app_user_password,
    delete_user,
    get_all_app_users,
    get_all_users,
    insert_app_user,
    insert_user,
    save_app_user,
    update_user,
)
from .user_sales_service import (
    get_user_catalog,
    get_user_options,
    prepare_sales_by_user_outputs,
)

# -----------------------------------------------------------------------------
# Dashboard and analytic module services
# -----------------------------------------------------------------------------

from .dashboard_service import prepare_dashboard_outputs
from .emisor_service import prepare_revenue_by_emisor_outputs
from .matrix_service import (
    get_available_reference_years,
    prepare_route_matrix_outputs,
)
from .route_service import (
    build_route_label,
    filter_route_coupons,
    get_emisor_options,
    prepare_route_analysis_outputs,
    safe_filename_part,
)
from .sales_service import (
    build_sales_period_label,
    compute_sales_kpis,
    get_sales_month_options,
    get_sales_year_options,
    prepare_sales_outputs,
)
from .tariff_service import (
    get_currency_options,
    prepare_tariff_style_outputs,
)
from .yield_service import prepare_yield_by_route_outputs

# -----------------------------------------------------------------------------
# Programmed revenue / volado services
# -----------------------------------------------------------------------------

from .programmed_revenue_common import (
    MESES,
    fmt_flight,
    normalize_summary_for_display,
)
from .programmed_revenue_module_service import (
    get_programmed_revenue_ui_options,
    prepare_programmed_revenue_module_outputs,
)
from .programmed_revenue_service import prepare_programmed_revenue_outputs
from .volado_service import prepare_volado_outputs

__all__ = [
    # Auth
    "authenticate_user",
    "create_app_user",
    "get_app_users",
    "hash_password",
    "reset_app_user_password",
    "update_app_user",
    "verify_password",

    # Admin / catalog
    "change_app_user_password",
    "delete_user",
    "get_all_app_users",
    "get_all_users",
    "insert_app_user",
    "insert_user",
    "save_app_user",
    "update_user",
    "get_user_catalog",
    "get_user_options",
    "prepare_sales_by_user_outputs",

    # Dashboard / analytics
    "prepare_dashboard_outputs",
    "prepare_revenue_by_emisor_outputs",
    "get_available_reference_years",
    "prepare_route_matrix_outputs",
    "build_route_label",
    "filter_route_coupons",
    "get_emisor_options",
    "prepare_route_analysis_outputs",
    "safe_filename_part",
    "build_sales_period_label",
    "compute_sales_kpis",
    "get_sales_month_options",
    "get_sales_year_options",
    "prepare_sales_outputs",
    "get_currency_options",
    "prepare_tariff_style_outputs",
    "prepare_yield_by_route_outputs",

    # Programmed / volado
    "MESES",
    "fmt_flight",
    "normalize_summary_for_display",
    "get_programmed_revenue_ui_options",
    "prepare_programmed_revenue_module_outputs",
    "prepare_programmed_revenue_outputs",
    "prepare_volado_outputs",
]