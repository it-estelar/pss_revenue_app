import streamlit as st

from services import (
    prepare_dashboard_outputs,
    prepare_programmed_revenue_outputs,
    prepare_revenue_by_emisor_outputs,
    prepare_tariff_style_outputs,
    prepare_volado_outputs,
    prepare_yield_by_route_outputs,
)
from ui import (
    render_admin_panel,
    render_dashboard,
    render_data_load_module,
    render_programmed_revenue_module,
    render_revenue_by_emisor,
    render_route_analysis,
    render_route_matrix,
    render_sales_by_user,
    render_sales_module,
    render_tariff_style,
    render_volado_module,
    render_yield_by_route,
)


# -----------------------------------------------------------------------------
# Context helpers
# -----------------------------------------------------------------------------

def _ctx(context: dict, key: str, required: bool = True, default=None):
    """
    Read a value from the shared app context.
    """
    value = context.get(key, default)
    if required and value is None:
        raise KeyError(f"Falta '{key}' en app context.")
    return value


def _get_report_period_builder(context: dict):
    """
    Return the optional report-period builder from app context.
    """
    return _ctx(context, "build_report_period", required=False)


def _build_report_period(context: dict, date_from, date_to):
    """
    Build the report period string if the helper exists in app context.
    """
    build_report_period = _get_report_period_builder(context)
    if build_report_period is None:
        return None
    return build_report_period(date_from, date_to)


# -----------------------------------------------------------------------------
# Date filter helpers
# -----------------------------------------------------------------------------

def _normalize_date_input(value):
    """
    Streamlit date_input may return a date or a tuple depending on configuration.
    Normalize it to a single date value.
    """
    if isinstance(value, tuple):
        return value[0] if value else None
    return value


def _render_plain_date_filters(module_key: str):
    """
    Render simple From/To date filters directly in the module body.
    """
    st.markdown("#### Filtros del módulo")

    c1, c2 = st.columns(2)
    with c1:
        date_from = st.date_input(
            "Desde",
            value=None,
            key=f"{module_key}_date_from",
        )
    with c2:
        date_to = st.date_input(
            "Hasta",
            value=None,
            key=f"{module_key}_date_to",
        )

    date_from = _normalize_date_input(date_from)
    date_to = _normalize_date_input(date_to)

    if date_from and date_to and date_from > date_to:
        st.error("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
        st.stop()

    return date_from, date_to


def _resolve_module_dates(module_key: str, plain_filters: bool = False):
    """
    Resolve the date filters for a module using either the plain inline filters
    or the shared UI date filter component.
    """
    if plain_filters:
        return _render_plain_date_filters(module_key)

    from ui import render_module_date_filters
    return render_module_date_filters(module_key)


# -----------------------------------------------------------------------------
# Shared module helpers
# -----------------------------------------------------------------------------

def _load_analytic_module_data(
    module_key: str,
    context: dict,
    include_report_period: bool = False,
    plain_filters: bool = False,
):
    """
    Load analytic module data through the shared DB-backed loader.
    """
    load_data_or_stop = _ctx(context, "load_data_or_stop")

    date_from, date_to = _resolve_module_dates(
        module_key=module_key,
        plain_filters=plain_filters,
    )

    df, coupons_long, kpis, tax_columns, routes = load_data_or_stop(date_from, date_to)

    payload = {
        "date_from": date_from,
        "date_to": date_to,
        "df": df,
        "coupons_long": coupons_long,
        "kpis": kpis,
        "tax_columns": tax_columns,
        "routes": routes,
        "report_period": None,
    }

    if include_report_period:
        payload["report_period"] = _build_report_period(context, date_from, date_to)

    return payload


def _show_module_shell(context: dict, kpis: dict):
    """
    Render the standard KPI shell for modules that show KPI cards.
    """
    show_kpis = _ctx(context, "show_kpis")
    show_kpis(kpis)
    st.divider()


def _render_top_n_and_table_controls(
    top_n_key: str,
    show_tables_key: str,
    top_n_label: str = "Top N",
    checkbox_label: str = "Mostrar tabla debajo del gráfico",
    top_n_default: int = 10,
    show_tables_default: bool = True,
):
    """
    Render the common Top N + show table controls used by chart modules.
    """
    c1, c2 = st.columns(2)

    with c1:
        top_n = st.slider(
            top_n_label,
            min_value=5,
            max_value=30,
            value=top_n_default,
            step=1,
            key=top_n_key,
        )

    with c2:
        show_tables = st.checkbox(
            checkbox_label,
            value=show_tables_default,
            key=show_tables_key,
        )

    return top_n, show_tables


# -----------------------------------------------------------------------------
# Module runners
# -----------------------------------------------------------------------------

def run_data_load_module(context: dict):
    """
    Run the CSV upload/load module.
    """
    preview_fn = _ctx(context, "preview_fn")
    execute_fn = _ctx(context, "execute_fn")
    history_fn = _ctx(context, "history_fn")

    render_data_load_module(
        preview_fn=preview_fn,
        execute_fn=execute_fn,
        history_fn=history_fn,
    )


def run_admin_panel_module(context: dict):
    """
    Run the admin/user catalog maintenance module.
    """
    render_admin_panel()


def run_dashboard_module(context: dict):
    """
    Run the dashboard module.
    """
    payload = _load_analytic_module_data(
        "dashboard",
        context,
        include_report_period=False,
        plain_filters=True,
    )

    df = payload["df"]
    coupons_long = payload["coupons_long"]
    kpis = payload["kpis"]

    prepared = prepare_dashboard_outputs(df, coupons_long)

    _show_module_shell(context, kpis)

    c1, c2 = st.columns([1, 1])
    with c1:
        top_n = st.slider(
            "Top N para gráficos",
            min_value=5,
            max_value=30,
            value=10,
            step=1,
            key="dashboard_top_n",
        )
    with c2:
        st.caption("Este módulo usa el rango de fechas seleccionado arriba.")

    render_dashboard(
        prepared["revenue_by_emisor_df"],
        prepared["yield_by_route_df"],
        prepared["routes_for_chart"],
        prepared["revenue_by_currency_class_df"],
        top_n,
    )


def run_revenue_by_emisor_module(context: dict):
    """
    Run the revenue-by-emisor module.
    """
    payload = _load_analytic_module_data(
        "revenue_by_emisor",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    df = payload["df"]
    coupons_long = payload["coupons_long"]
    kpis = payload["kpis"]
    report_period = payload["report_period"]

    prepared = prepare_revenue_by_emisor_outputs(df, coupons_long)

    _show_module_shell(context, kpis)

    top_n, show_tables = _render_top_n_and_table_controls(
        top_n_key="revenue_by_emisor_top_n",
        show_tables_key="revenue_by_emisor_show_tables",
    )

    render_revenue_by_emisor(
        prepared["revenue_by_emisor_df"],
        coupons_long,
        prepared["emisor_filter_options"],
        top_n,
        show_tables,
        report_period=report_period,
    )


def run_tariff_style_module(context: dict):
    """
    Run the tariff-style module.
    """
    safe_unique_sorted = _ctx(context, "safe_unique_sorted")

    payload = _load_analytic_module_data(
        "tariff_style",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    df = payload["df"]
    kpis = payload["kpis"]
    report_period = payload["report_period"]

    prepared = prepare_tariff_style_outputs(
        df,
        safe_unique_sorted,
    )

    _show_module_shell(context, kpis)

    show_tables = st.checkbox(
        "Mostrar tabla debajo del gráfico",
        value=True,
        key="tariff_style_show_tables",
    )

    render_tariff_style(
        prepared["revenue_by_currency_class_df"],
        prepared["currency_options"],
        show_tables,
        report_period=report_period,
    )


def run_yield_by_route_module(context: dict):
    """
    Run the yield-by-route module.
    """
    payload = _load_analytic_module_data(
        "yield_by_route",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    coupons_long = payload["coupons_long"]
    kpis = payload["kpis"]
    report_period = payload["report_period"]

    prepared = prepare_yield_by_route_outputs(coupons_long)

    _show_module_shell(context, kpis)

    top_n, show_tables = _render_top_n_and_table_controls(
        top_n_key="yield_by_route_top_n",
        show_tables_key="yield_by_route_show_tables",
    )

    render_yield_by_route(
        prepared["yield_by_route_df"],
        top_n,
        show_tables,
        report_period=report_period,
    )


def run_route_analysis_module(context: dict):
    """
    Run the route-analysis module.
    """
    payload = _load_analytic_module_data(
        "route_analysis",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    coupons_long = payload["coupons_long"]
    routes = payload["routes"]
    report_period = payload["report_period"]

    route_options = routes if routes else []

    show_tables = st.checkbox(
        "Mostrar tabla de clases debajo del gráfico",
        value=True,
        key="route_analysis_show_tables",
    )

    render_route_analysis(
        coupons_long,
        route_options,
        show_tables,
        report_period=report_period,
    )


def run_programmed_revenue_module(context: dict):
    """
    Run the programmed revenue module.

    This module intentionally uses its own preparation path because it relies
    on a different data flow than the standard analytic modules.
    """
    prepared = prepare_programmed_revenue_outputs()
    render_programmed_revenue_module(prepared["raw_df"])


def run_route_matrix_module(context: dict):
    """
    Run the purchase-vs-programmed heatmap module.
    """
    load_data_or_stop = _ctx(context, "load_data_or_stop")
    _, coupons_long, _, _, routes = load_data_or_stop(None, None)

    route_options = routes if routes else []
    render_route_matrix(coupons_long, route_options)


def run_sales_module(context: dict):
    """
    Run the sales module.
    """
    payload = _load_analytic_module_data(
        "sales",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    df = payload["df"]
    coupons_long = payload["coupons_long"]
    kpis = payload["kpis"]
    report_period = payload["report_period"]

    _show_module_shell(context, kpis)

    render_sales_module(
        df,
        coupons_long,
        report_period=report_period,
    )


def run_volado_module(context: dict):
    """
    Run the volado module.

    This module intentionally uses its own preparation path because it relies
    on a different data flow than the standard analytic modules.
    """
    date_from, date_to = _render_plain_date_filters("volado")
    report_period = _build_report_period(context, date_from, date_to)

    prepared = prepare_volado_outputs(date_from=date_from, date_to=date_to)

    kpis = {
        "total_revenue": prepared["kpis"]["total_revenue"],
        "total_coupons": prepared["kpis"]["total_coupons"],
        "unique_tickets": prepared["kpis"]["total_routes"],
    }

    _show_module_shell(context, kpis)

    top_n, show_tables = _render_top_n_and_table_controls(
        top_n_key="volado_top_n",
        show_tables_key="volado_show_tables",
    )

    render_volado_module(
        prepared["volado_df"],
        top_n,
        show_tables,
        report_period=report_period,
    )


def run_sales_by_user_module(context: dict):
    """
    Run the sales-by-user module.
    """
    payload = _load_analytic_module_data(
        "sales_by_user",
        context,
        include_report_period=True,
        plain_filters=True,
    )

    df = payload["df"]
    kpis = payload["kpis"]
    report_period = payload["report_period"]

    _show_module_shell(context, kpis)

    render_sales_by_user(
        df,
        report_period=report_period,
    )