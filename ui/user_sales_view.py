import pandas as pd
import streamlit as st

from charts.user_sales_charts import (
    chart_user_emisor,
    chart_user_revenue,
)
from exporters import build_single_table_pdf, single_df_to_excel_bytes
from services import prepare_sales_by_user_outputs

from .shared import (
    build_pdf_subtitle,
    metric_text_int,
    metric_text_money,
    render_export_buttons,
    render_paginated_table,
    render_section_title,
    select_table_style,
)


def _build_sales_by_user_pdf_df(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df is None or summary_df.empty:
        return pd.DataFrame(
            columns=["USUARIO", "AGENTE", "ESTACION", "REVENUE", "TICKETS", "CUPONES"]
        )

    pdf_df = summary_df.copy()

    for col in ["REVENUE", "TICKETS", "CUPONES"]:
        if col not in pdf_df.columns:
            pdf_df[col] = 0

    total_row = pd.DataFrame(
        [
            {
                "USUARIO": "TOTAL",
                "AGENTE": "",
                "ESTACION": "",
                "REVENUE": float(pd.to_numeric(pdf_df["REVENUE"], errors="coerce").fillna(0).sum()),
                "TICKETS": int(pd.to_numeric(pdf_df["TICKETS"], errors="coerce").fillna(0).sum()),
                "CUPONES": int(pd.to_numeric(pdf_df["CUPONES"], errors="coerce").fillna(0).sum()),
            }
        ]
    )

    return pd.concat([pdf_df, total_row], ignore_index=True)


def render_sales_by_user(df, report_period=None):
    render_section_title("Sales by User")

    top_n = st.slider(
        "Top emisores",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
        key="sales_by_user_top_n",
    )

    initial = prepare_sales_by_user_outputs(df, selected_users=None, top_n_emisores=top_n)
    user_options = initial["user_options"]

    if not user_options:
        st.warning("No hay usuarios activos en el catálogo del Admin Panel.")
        return

    selected_users = st.multiselect(
        "Usuarios",
        options=user_options,
        default=[],
        key="sales_by_user_users",
        help="Si no seleccionas usuarios, el módulo mostrará todos los usuarios activos con match en la data.",
    )

    prepared = prepare_sales_by_user_outputs(
        df,
        selected_users=selected_users,
        top_n_emisores=top_n,
    )

    summary_df = prepared["summary_df"]
    emisor_df = prepared["emisor_df"]
    kpis = prepared["kpis"]
    coverage = prepared["coverage"]

    if summary_df.empty:
        st.warning("No hay ventas para los usuarios seleccionados.")
        return

    if coverage["unmatched_revenue"] > 0:
        st.info(
            f"Hay revenue sin mapear contra el catálogo de usuarios: {metric_text_money(coverage['unmatched_revenue'])} "
            f"en {metric_text_int(coverage['unmatched_tickets'])} tickets."
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Revenue", metric_text_money(kpis["total_revenue"]))
    with c2:
        st.metric("Tickets", metric_text_int(kpis["total_tickets"]))
    with c3:
        st.metric("Cupones", metric_text_int(kpis["total_coupons"]))
    with c4:
        st.metric("Usuarios", metric_text_int(kpis["total_users"]))

    st.markdown("")

    st.plotly_chart(
        chart_user_revenue(summary_df),
        use_container_width=True,
        config={"displaylogo": False},
    )

    st.plotly_chart(
        chart_user_emisor(emisor_df),
        use_container_width=True,
        config={"displaylogo": False},
    )

    st.markdown("### Resumen por Usuario")

    table_style = select_table_style(
        "sales_by_user_table_style",
        default="Executive Blue",
    )

    render_paginated_table(
        summary_df,
        table_style,
        "sales_by_user_summary",
        default_rows_per_page=25,
    )

    pdf_df = _build_sales_by_user_pdf_df(summary_df)
    excel_bytes = single_df_to_excel_bytes(pdf_df, "sales_by_user_summary")

    subtitle = build_pdf_subtitle(
        "Resumen de ventas por usuario emisor.",
        report_period if report_period else "",
    )

    pdf_bytes = build_single_table_pdf(
        title="Sales by User",
        df=pdf_df,
        styled=True,
        subtitle=subtitle,
        kpi_pairs=[
            ("Revenue", metric_text_money(kpis["total_revenue"])),
            ("Tickets", metric_text_int(kpis["total_tickets"])),
            ("Cupones", metric_text_int(kpis["total_coupons"])),
            ("Usuarios", metric_text_int(kpis["total_users"])),
        ],
    )

    render_export_buttons(
        excel_bytes,
        "sales_by_user_summary.xlsx",
        pdf_bytes,
        "sales_by_user_summary.pdf",
        "sales_by_user_excel",
        "sales_by_user_pdf",
    )