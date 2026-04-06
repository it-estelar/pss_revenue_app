from __future__ import annotations

import pandas as pd
import streamlit as st

from exporters import build_single_table_pdf, single_df_to_excel_bytes
from services import (
    MESES,
    get_programmed_revenue_ui_options,
    prepare_programmed_revenue_module_outputs,
)

from .programmed_revenue_charts import (
    build_programmed_revenue_summary_chart_png,
    render_programmed_revenue_summary_chart,
)
from .programmed_revenue_tables import (
    inject_exec_table_css,
    render_flight_ticket_checkboxes,
)
from .shared import (
    build_pdf_subtitle,
    metric_text_int,
    metric_text_money,
    render_export_buttons,
    render_paginated_table,
)


def _build_programmed_revenue_pdf_df(display_summary: pd.DataFrame) -> pd.DataFrame:
    pdf_df = display_summary.copy()

    expected_cols = [
        "Fecha",
        "Origen",
        "Destino",
        "Vuelo",
        "Cupones",
        "Tickets",
        "Ingreso",
        "TKTT Ingreso",
        "EMDA Ingreso",
    ]

    numeric_cols = {"Cupones", "Tickets", "Ingreso", "TKTT Ingreso", "EMDA Ingreso"}

    for col in expected_cols:
        if col not in pdf_df.columns:
            pdf_df[col] = 0 if col in numeric_cols else ""

    pdf_df = pdf_df[expected_cols].copy()

    total_ingreso = float(pd.to_numeric(pdf_df["Ingreso"], errors="coerce").fillna(0).sum())

    if total_ingreso > 0:
        pdf_df["% Ingreso"] = (
            pd.to_numeric(pdf_df["Ingreso"], errors="coerce").fillna(0) / total_ingreso
        ) * 100
    else:
        pdf_df["% Ingreso"] = 0.0

    pdf_df["% Ingreso"] = pdf_df["% Ingreso"].round(1)

    total_row = pd.DataFrame(
        [
            {
                "Fecha": "TOTAL MES",
                "Origen": "",
                "Destino": "",
                "Vuelo": "",
                "Cupones": int(pd.to_numeric(pdf_df["Cupones"], errors="coerce").fillna(0).sum()),
                "Tickets": int(pd.to_numeric(pdf_df["Tickets"], errors="coerce").fillna(0).sum()),
                "Ingreso": float(pd.to_numeric(pdf_df["Ingreso"], errors="coerce").fillna(0).sum()),
                "TKTT Ingreso": float(pd.to_numeric(pdf_df["TKTT Ingreso"], errors="coerce").fillna(0).sum()),
                "EMDA Ingreso": float(pd.to_numeric(pdf_df["EMDA Ingreso"], errors="coerce").fillna(0).sum()),
                "% Ingreso": 100.0 if total_ingreso > 0 else 0.0,
            }
        ]
    )

    return pd.concat([pdf_df, total_row], ignore_index=True)


def _build_programmed_revenue_excel_df(display_summary: pd.DataFrame) -> pd.DataFrame:
    return _build_programmed_revenue_pdf_df(display_summary).copy()


def render_programmed_revenue_module(df: pd.DataFrame):
    inject_exec_table_css()

    st.subheader("Programmed Revenue by Flight")

    if df is None or df.empty:
        st.warning("No hay datos disponibles para este módulo.")
        return

    options = get_programmed_revenue_ui_options(df)

    route_options = options["route_options"]
    year_options = options["year_options"]
    month_options = options["month_options"]

    if not route_options or not year_options or not month_options:
        st.warning("No hay datos programados suficientes para construir este módulo.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        selected_route = st.selectbox(
            "Ruta",
            route_options,
            index=route_options.index(options["default_route"]) if options["default_route"] in route_options else 0,
        )

    with c2:
        selected_year = st.selectbox(
            "Año",
            year_options,
            index=year_options.index(options["default_year"]) if options["default_year"] in year_options else len(year_options) - 1,
        )

    with c3:
        selected_month = st.selectbox(
            "Mes",
            month_options,
            index=month_options.index(options["default_month"]) if options["default_month"] in month_options else max(0, len(month_options) - 1),
            format_func=lambda x: MESES.get(x, str(x)),
        )

    prepared = prepare_programmed_revenue_module_outputs(
        df=df,
        route=selected_route,
        month=int(selected_month),
        year=int(selected_year),
    )

    summary = prepared["summary"]
    detail = prepared["detail"]
    validation = prepared["validation"]
    validation_display = prepared["validation_display"]
    display_summary = prepared["display_summary"]
    kpis = prepared["kpis"]
    title = prepared["title"]

    st.markdown(f"## {title}")

    if summary.empty:
        st.warning("No hay datos para esa combinación de ruta, mes y año.")
        with st.expander("Validaciones"):
            st.write(validation)
        return

    render_programmed_revenue_summary_chart(summary)

    st.markdown("### Detalle de vuelos")

    table_style = st.selectbox(
        "Estilo de tabla",
        ["Executive Blue", "Soft Gray", "Standard"],
        index=0,
        key="programmed_revenue_table_style",
    )

    render_paginated_table(
        display_summary,
        table_style,
        "programmed_revenue_flight_summary",
        default_rows_per_page=10,
    )

    render_flight_ticket_checkboxes(detail)

    with st.expander("Validaciones"):
        st.write(validation_display)

    excel_df = _build_programmed_revenue_excel_df(display_summary)
    excel_bytes = single_df_to_excel_bytes(excel_df, sheet_name="programmed_revenue")

    pdf_df = _build_programmed_revenue_pdf_df(display_summary)
    chart_png = build_programmed_revenue_summary_chart_png(summary, top_n=5)

    vuelos_operados = len(display_summary.index)
    ingreso_promedio_vuelo = (
        kpis["total_ingreso"] / vuelos_operados if vuelos_operados else 0
    )

    pdf_subtitle = build_pdf_subtitle(
        (
            "Revenue programado prorrateado por cupón + EMDA relacionado. "
            f"Ruta: {selected_route}. "
            f"Vuelos operados: {vuelos_operados}. "
            f"Ingreso promedio por vuelo: {ingreso_promedio_vuelo:,.0f} USD."
        ),
        None,
    )

    pdf_bytes = build_single_table_pdf(
        title=title,
        df=pdf_df,
        styled=True,
        subtitle=pdf_subtitle,
        chart_png=chart_png,
        kpi_pairs=[
            ("Ingreso programado", metric_text_money(kpis["total_ingreso"])),
            ("Cupones", metric_text_int(kpis["total_cupones"])),
            ("Tickets", metric_text_int(kpis["total_tickets"])),
            ("EMDA sin match", metric_text_int(kpis["unmatched_emda"])),
        ],
        chart_first_page=True,
    )

    st.markdown("##### Exportación programmed revenue")
    render_export_buttons(
        excel_bytes,
        f"programmed_revenue_{selected_route}_{selected_year}_{selected_month}.xlsx",
        pdf_bytes,
        f"programmed_revenue_{selected_route}_{selected_year}_{selected_month}.pdf",
        "programmed_revenue_excel",
        "programmed_revenue_pdf",
    )