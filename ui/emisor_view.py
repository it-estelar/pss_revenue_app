import streamlit as st

from charts import chart_top_emisores, chart_top_routes, build_top_routes_chart_png
from exporters import build_single_table_pdf, single_df_to_excel_bytes
from reports import build_routes_by_emisor

from .shared import (
    build_pdf_subtitle,
    render_export_buttons,
    render_paginated_table,
    render_table,
)


def _build_routes_pdf_title(selected_emisores):
    if not selected_emisores:
        return "Rutas vendidas por emisor - Todos los emisores"

    if len(selected_emisores) == 1:
        return f"Rutas vendidas por emisor - {selected_emisores[0]}"

    return "Rutas vendidas por emisor - Emisores seleccionados"


def _build_routes_pdf_subtitle(selected_emisores, report_period):
    if not selected_emisores:
        base = "Incluye las rutas vendidas por todos los emisores del período."
    elif len(selected_emisores) == 1:
        base = f"Incluye las rutas vendidas por el emisor {selected_emisores[0]}."
    else:
        preview = ", ".join(selected_emisores[:5])
        suffix = " ..." if len(selected_emisores) > 5 else ""
        base = f"Incluye las rutas vendidas por los emisores: {preview}{suffix}."

    return build_pdf_subtitle(base, report_period)


def _build_routes_kpis(routes_by_emisor_df):
    if routes_by_emisor_df is None or routes_by_emisor_df.empty:
        return []

    work = routes_by_emisor_df.copy()
    work = work[work["Ruta"].astype(str).str.upper() != "TOTAL"].copy()

    if work.empty:
        return []

    total_revenue = float(work["Revenue"].sum()) if "Revenue" in work.columns else 0
    total_cupones = int(work["Cantidad_de_Cupones"].sum()) if "Cantidad_de_Cupones" in work.columns else 0
    total_rutas = int(work["Ruta"].nunique()) if "Ruta" in work.columns else 0

    promedio_por_ruta = total_revenue / total_rutas if total_rutas else 0

    return [
        ("Revenue total", f"{total_revenue:,.0f} USD"),
        ("Cupones", f"{total_cupones:,.0f}"),
        ("Rutas", f"{total_rutas:,.0f}"),
        ("Promedio por ruta", f"{promedio_por_ruta:,.0f} USD"),
    ]


def render_revenue_by_emisor(
    revenue_by_emisor_df,
    coupons_long,
    emisor_filter_options,
    top_n,
    show_tables,
    report_period=None,
):
    st.markdown('<div class="section-title">Revenue by Emisor</div>', unsafe_allow_html=True)

    st.plotly_chart(
        chart_top_emisores(revenue_by_emisor_df, top_n=top_n),
        use_container_width=True,
        config={"displaylogo": False},
    )

    table_style = "Executive Blue"

    if show_tables:
        table_style = st.selectbox(
            "Estilo de tabla",
            ["Standard", "Executive Blue", "Soft Gray"],
            index=1,
            key="revenue_emisor_table_style",
        )
        render_paginated_table(
            revenue_by_emisor_df,
            table_style,
            "revenue_emisor",
            default_rows_per_page=25,
        )

    excel_bytes = single_df_to_excel_bytes(revenue_by_emisor_df, "revenue_by_emisor")
    pdf_bytes = build_single_table_pdf(
        "Revenue by Emisor",
        revenue_by_emisor_df,
        styled=False,
        max_rows=5000,
        subtitle=build_pdf_subtitle(None, report_period),
    )

    render_export_buttons(
        excel_bytes,
        "revenue_by_emisor.xlsx",
        pdf_bytes,
        "revenue_by_emisor.pdf",
        "emisor_excel_new",
        "emisor_pdf_new",
    )

    st.markdown("---")
    st.markdown("#### Rutas vendidas por emisor")

    selected_emisores = st.multiselect(
        "Emisor(es) para este reporte",
        options=emisor_filter_options,
        default=[],
        key="revenue_by_emisor_route_filter",
        help="Déjalo vacío para incluir todos los emisores. Puedes seleccionar uno o varios.",
    )

    if selected_emisores:
        st.markdown(f"**Emisor(es) filtrado(s):** {len(selected_emisores)}")
        st.caption(", ".join(selected_emisores))
    else:
        st.caption("Incluye todos los emisores disponibles.")

    routes_by_emisor_df = build_routes_by_emisor(coupons_long, selected_emisores)

    if routes_by_emisor_df.empty:
        st.warning("No hay rutas para los emisores seleccionados en el período actual.")
        return

    st.plotly_chart(
        chart_top_routes(routes_by_emisor_df, top_n=top_n),
        use_container_width=True,
        config={"displaylogo": False},
    )

    if show_tables:
        st.markdown("##### Detalle de rutas por emisor")
        render_table(
            routes_by_emisor_df,
            table_style,
            "routes_by_emisor",
        )

    routes_excel_bytes = single_df_to_excel_bytes(
        routes_by_emisor_df,
        "routes_by_emisor",
    )

    chart_title = (
        f"Top {top_n} rutas por revenue"
        if not selected_emisores
        else f"Top {top_n} rutas por revenue - emisores seleccionados"
    )
    routes_chart_png = build_top_routes_chart_png(
        routes_by_emisor_df,
        top_n=top_n,
        title=chart_title,
    )

    routes_pdf_bytes = build_single_table_pdf(
        title=_build_routes_pdf_title(selected_emisores),
        df=routes_by_emisor_df,
        styled=True,
        max_rows=5000,
        subtitle=_build_routes_pdf_subtitle(selected_emisores, report_period),
        chart_png=routes_chart_png,
        kpi_pairs=_build_routes_kpis(routes_by_emisor_df),
        chart_first_page=True,
    )

    st.markdown("##### Exportación rutas por emisor")
    render_export_buttons(
        routes_excel_bytes,
        "routes_by_emisor.xlsx",
        routes_pdf_bytes,
        "routes_by_emisor.pdf",
        "routes_by_emisor_excel",
        "routes_by_emisor_pdf",
    )