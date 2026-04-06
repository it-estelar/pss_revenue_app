import streamlit as st

from charts import (
    build_sales_route_month_chart_png,
    chart_sales_by_month,
    chart_sales_by_week,
    chart_sales_route_month,
)
from exporters import build_single_table_pdf, df_to_excel_bytes
from services import (
    build_sales_period_label,
    get_sales_month_options,
    get_sales_year_options,
    prepare_sales_outputs,
)

from .shared import (
    build_pdf_subtitle,
    metric_text_int,
    metric_text_money,
    render_block_title,
    render_export_buttons,
    render_section_title,
    render_table,
    select_table_style,
)


def render_sales_module(df, coupons_long, report_period=None):
    render_section_title("Sales")

    years = get_sales_year_options(df)
    if not years:
        st.warning("No hay años disponibles para el módulo de ventas.")
        return

    c1, c2 = st.columns([1, 1])
    with c1:
        selected_year = st.selectbox(
            "Año",
            options=years,
            index=len(years) - 1,
            key="sales_year_filter",
        )

    month_options = get_sales_month_options(df, selected_year)
    if not month_options:
        st.warning("No hay meses disponibles para el año seleccionado.")
        return

    month_labels = [m["label"] for m in month_options]
    default_month_index = len(month_labels) - 1

    with c2:
        selected_month_label = st.selectbox(
            "Mes",
            options=month_labels,
            index=default_month_index,
            key="sales_month_filter",
        )

    selected_month_value = next(
        m["value"] for m in month_options if m["label"] == selected_month_label
    )

    prepared = prepare_sales_outputs(df, coupons_long, selected_year, selected_month_value)
    monthly_df = prepared["monthly_df"]
    weekly_df = prepared["weekly_df"]
    route_month_df = prepared["route_month_df"]
    kpis = prepared["kpis"]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Revenue año", metric_text_money(kpis["total_year_revenue"]))
    metric_cols[1].metric("Cupones año", metric_text_int(kpis["total_year_coupons"]))
    metric_cols[2].metric(
        f"Revenue {selected_month_label}",
        metric_text_money(kpis["total_month_revenue"]),
    )
    metric_cols[3].metric(
        f"Cupones {selected_month_label}",
        metric_text_int(kpis["total_month_coupons"]),
    )

    table_style = select_table_style(
        "sales_table_style",
        default="Executive Blue",
    )

    render_block_title("Resumen anual por mes")
    st.plotly_chart(
        chart_sales_by_month(monthly_df),
        use_container_width=True,
        config={"displaylogo": False},
    )
    render_table(monthly_df, table_style, "sales_monthly")

    render_block_title(f"Resumen semanal de {selected_month_label}")
    st.plotly_chart(
        chart_sales_by_week(weekly_df, selected_month_label),
        use_container_width=True,
        config={"displaylogo": False},
    )
    render_table(weekly_df, table_style, "sales_weekly")

    sales_period = build_sales_period_label(selected_year, selected_month_label)

    weekly_excel_bytes = df_to_excel_bytes(
        {
            "sales_monthly": monthly_df,
            "sales_weekly": weekly_df,
        }
    )

    weekly_pdf_bytes = build_single_table_pdf(
        title=f"Ventas semanales - {selected_month_label} {selected_year}",
        subtitle=build_pdf_subtitle(
            "Incluye revenue total, cupones y segregación por tipo de transacción.",
            sales_period if not report_period else f"{report_period} | {sales_period}",
        ),
        df=weekly_df,
        styled=True,
        max_rows=5000,
    )

    st.markdown("##### Exportación resumen semanal")
    render_export_buttons(
        weekly_excel_bytes,
        f"sales_{selected_year}_{selected_month_value:02d}.xlsx",
        weekly_pdf_bytes,
        f"sales_weekly_{selected_year}_{selected_month_value:02d}.pdf",
        "sales_excel",
        "sales_pdf",
    )

    st.markdown("---")

    render_block_title(
        "Revenue por ruta y por mes",
        "Este bloque usa las rutas normalizadas del detalle de cupones y agrupa ambos sentidos.",
    )
    st.plotly_chart(
        chart_sales_route_month(route_month_df, top_n=10),
        use_container_width=True,
        config={"displaylogo": False},
    )
    render_table(route_month_df, table_style, "sales_route_month")

    route_month_chart_png = build_sales_route_month_chart_png(route_month_df, top_n=10)
    annual_period = f"Período anual: {selected_year}"

    route_excel_bytes = df_to_excel_bytes(
        {
            "sales_route_month": route_month_df,
        }
    )

    route_pdf_bytes = build_single_table_pdf(
        title=f"Revenue por Ruta y Mes - {selected_year}",
        subtitle=build_pdf_subtitle(
            "Incluye gráfico y tabla de ingreso por ruta y por mes.",
            annual_period if not report_period else f"{report_period} | {annual_period}",
        ),
        df=route_month_df,
        styled=True,
        max_rows=5000,
        chart_png=route_month_chart_png,
        chart_first_page=True,
    )

    st.markdown("##### Exportación revenue por ruta y mes")
    render_export_buttons(
        route_excel_bytes,
        f"sales_route_month_{selected_year}.xlsx",
        route_pdf_bytes,
        f"sales_route_month_{selected_year}.pdf",
        "sales_route_month_excel",
        "sales_route_month_pdf",
    )