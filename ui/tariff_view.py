import streamlit as st

from charts import chart_currency_class_mix
from exporters import build_single_table_pdf, single_df_to_excel_bytes
from reports import build_tariff_style_report

from .shared import (
    build_pdf_subtitle,
    render_export_buttons,
    render_paginated_table,
    render_table,
)


def _build_tariff_pdf_title(selected_currencies):
    if not selected_currencies:
        return "EMISIONES POR CLASE TARIFARIA - TODAS LAS MONEDAS"

    if len(selected_currencies) == 1:
        return f"EMISIONES POR CLASE TARIFARIA - {selected_currencies[0]}"

    return "EMISIONES POR CLASE TARIFARIA - MONEDAS SELECCIONADAS"


def render_tariff_style(revenue_by_currency_class_df, currency_options, show_tables, report_period=None):
    st.markdown('<div class="section-title">Tariff Style</div>', unsafe_allow_html=True)

    selected_currencies = st.multiselect(
        "Moneda(s) para este reporte",
        options=currency_options,
        default=[],
        key="tariff_currency_filter",
        help="Déjalo vacío para incluir todas las monedas.",
    )

    tariff_style_df = build_tariff_style_report(
        revenue_by_currency_class_df,
        selected_currency=selected_currencies,
    )

    st.plotly_chart(
        chart_currency_class_mix(revenue_by_currency_class_df, selected_currencies),
        use_container_width=True,
        config={"displaylogo": False},
    )

    if selected_currencies:
        st.markdown(f"**Moneda(s) filtrada(s):** {len(selected_currencies)}")
        st.caption(", ".join(selected_currencies))
    else:
        st.caption("Incluye todas las monedas disponibles.")

    if show_tables:
        table_style = st.selectbox(
            "Estilo de tabla",
            ["Standard", "Executive Blue", "Soft Gray"],
            index=1,
            key="tariff_style_table_style",
        )

        if selected_currencies:
            render_paginated_table(
                tariff_style_df,
                table_style,
                "tariff_style",
                default_rows_per_page=25,
            )
        else:
            render_table(tariff_style_df, table_style, "tariff_style")

    excel_bytes = single_df_to_excel_bytes(tariff_style_df, "tariff_style_report")
    pdf_title = _build_tariff_pdf_title(selected_currencies)

    pdf_bytes = build_single_table_pdf(
        pdf_title,
        tariff_style_df,
        styled=True,
        max_rows=5000,
        subtitle=build_pdf_subtitle(None, report_period),
    )

    render_export_buttons(
        excel_bytes,
        "tariff_style_report.xlsx",
        pdf_bytes,
        "tariff_style_report.pdf",
        "tariff_excel_new",
        "tariff_pdf_new",
    )