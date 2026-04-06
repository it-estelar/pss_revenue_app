import streamlit as st

from charts import build_route_class_chart_png, chart_route_class_mix
from exporters import build_single_table_pdf, df_to_excel_bytes
from services import get_emisor_options, prepare_route_analysis_outputs

from .shared import (
    build_pdf_subtitle,
    render_block_title,
    render_export_buttons,
    render_paginated_table,
    render_report_period,
    render_section_title,
    render_selection_summary,
    render_table,
    select_table_style,
)


def render_route_analysis(coupons_long, route_options, show_tables, report_period=None):
    render_section_title("Route Analysis")

    if coupons_long.empty or not route_options:
        st.warning("No hay rutas disponibles en el archivo actual.")
        return

    emisor_options = get_emisor_options(coupons_long)

    filter_left, filter_right = st.columns(2)
    with filter_left:
        selected_routes = st.multiselect(
            "Ruta(s) para este reporte",
            options=route_options,
            default=[],
            key="route_analysis_filter",
            help="Déjalo vacío para incluir todas las rutas. Puedes seleccionar una o varias.",
        )

    with filter_right:
        selected_emisores = st.multiselect(
            "Filtrar por emisor o grupo de emisores",
            options=emisor_options,
            default=[],
            key="route_analysis_emisor_filter",
            help="Déjalo vacío para incluir todos los emisores.",
        )

    table_style = select_table_style(
        "route_analysis_table_style",
        default="Executive Blue",
        help_text="Executive Blue se ve más corporativo. Soft Gray se ve más limpio y suave.",
    )

    prepared = prepare_route_analysis_outputs(
        coupons_long,
        selected_routes,
        selected_emisores,
    )

    filtered_coupons = prepared["filtered_coupons"]
    route_label = prepared["route_label"]
    route_emisor_df = prepared["route_emisor_df"]
    route_class_df = prepared["route_class_df"]
    filename_stub = prepared["filename_stub"]

    if filtered_coupons.empty:
        st.warning("No hay ventas para la combinación de rutas y emisores seleccionada.")
        return

    route_chart_png = build_route_class_chart_png(route_class_df, route_label, top_n=10)

    render_selection_summary(
        "Ruta(s) seleccionada(s)",
        selected_routes,
        empty_text="Incluye todas las rutas.",
    )
    render_report_period(report_period)

    if not selected_routes:
        st.markdown(
            "Se incluyen todas las rutas disponibles en el período seleccionado. "
            "Cada ruta está normalizada y agrupa ambos sentidos."
        )
    elif len(selected_routes) == 1:
        st.markdown("Esta ruta agrupa ambos sentidos de la operación.")
    else:
        st.markdown(
            "Las rutas seleccionadas se analizan en conjunto. "
            "Cada ruta ya está normalizada y agrupa ambos sentidos."
        )

    render_selection_summary(
        "Emisor(es) filtrado(s)",
        selected_emisores,
        empty_text="Incluye todos los emisores.",
    )

    render_block_title("Mix de clases por rutas seleccionadas")
    st.plotly_chart(
        chart_route_class_mix(route_class_df, route_name=route_label, top_n=10),
        use_container_width=True,
        config={"displaylogo": False},
    )

    if show_tables:
        render_block_title("Detalle de clases por ruta")
        render_table(route_class_df, table_style, "route_clases")

        render_block_title("Emisores por ruta")
        render_paginated_table(
            route_emisor_df,
            table_style,
            "route_emisores",
            default_rows_per_page=25,
        )

    excel_bytes = df_to_excel_bytes(
        {
            "route_emisores": route_emisor_df,
            "route_clases": route_class_df,
        }
    )

    if selected_routes:
        subtitle = f"Rutas seleccionadas: {', '.join(selected_routes)}."
    else:
        subtitle = "Rutas seleccionadas: todas."

    if not selected_routes:
        subtitle += " Análisis consolidado de todas las rutas normalizadas."
    elif len(selected_routes) == 1:
        subtitle += " Ruta normalizada que agrupa ambos sentidos de la operación."
    else:
        subtitle += " Análisis consolidado de rutas normalizadas."

    if selected_emisores:
        subtitle += f" Filtro de emisor aplicado: {', '.join(selected_emisores[:5])}"
        if len(selected_emisores) > 5:
            subtitle += " ..."

    pdf_bytes = build_single_table_pdf(
        title=f"Top Emisores por Ruta - {route_label}",
        subtitle=build_pdf_subtitle(subtitle, report_period),
        df=route_emisor_df,
        styled=True,
        max_rows=5000,
        chart_png=route_chart_png,
        chart_first_page=True,
    )

    render_export_buttons(
        excel_bytes,
        f"route_report_{filename_stub}.xlsx",
        pdf_bytes,
        f"route_report_{filename_stub}.pdf",
        "route_excel_new",
        "route_pdf_new",
    )