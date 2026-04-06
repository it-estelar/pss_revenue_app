from __future__ import annotations

from collections.abc import Callable

from .module_router import (
    run_admin_panel_module,
    run_dashboard_module,
    run_data_load_module,
    run_programmed_revenue_module,
    run_revenue_by_emisor_module,
    run_route_analysis_module,
    run_route_matrix_module,
    run_sales_by_user_module,
    run_sales_module,
    run_tariff_style_module,
    run_volado_module,
    run_yield_by_route_module,
)


ModuleRunner = Callable[[dict], None]


def get_module_registry() -> dict[str, ModuleRunner]:
    """
    Return the mapping between sidebar module labels and router runner functions.

    This is the single source of truth for module dispatch.
    The keys must stay aligned with navigation.MODULE_LABELS.
    """
    return {
        "Dashboard": run_dashboard_module,
        "Revenue by Emisor": run_revenue_by_emisor_module,
        "Tariff Style": run_tariff_style_module,
        "Yield by Route": run_yield_by_route_module,
        "Volado": run_volado_module,
        "Programmed Revenue by Flight": run_programmed_revenue_module,
        "Route Analysis": run_route_analysis_module,
        "Purchase vs Programmed Heatmap": run_route_matrix_module,
        "Sales": run_sales_module,
        "Sales by User": run_sales_by_user_module,
        "Admin Panel": run_admin_panel_module,
        "Data Load": run_data_load_module,
    }


def get_module_runner(module_name: str) -> ModuleRunner | None:
    """
    Resolve a module label to its corresponding runner function.
    Returns None if the module label is not registered.
    """
    return get_module_registry().get(module_name)