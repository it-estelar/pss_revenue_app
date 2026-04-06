import streamlit as st

from charts import chart_yield_by_route
from exporters import build_single_table_pdf, single_df_to_excel_bytes

from .shared import build_pdf_subtitle, render_export_buttons, render_table


def render_yield_by_route(yield_by_route_df, top_n, show_tables, report_period=None):
    st.markdown('<div class="section-title">Yield by Route</div>', unsafe_allow_html=True)

    st.plotly_chart(
        chart_yield_by_route(yield_by_route_df, top_n=top_n),
        use_container_width=True,
        config={"displaylogo": False},
    )

    if show_tables:
        table_style = st.selectbox(
            "Estilo de tabla",
            ["Standard", "Executive Blue", "Soft Gray"],
            index=1,
            key="yield_by_route_table_style",
        )
        render_table(yield_by_route_df, table_style, "yield_by_route")

    excel_bytes = single_df_to_excel_bytes(yield_by_route_df, "yield_by_route")
    pdf_bytes = build_single_table_pdf(
        "Yield by Route",
        yield_by_route_df,
        styled=False,
        max_rows=5000,
        subtitle=build_pdf_subtitle(None, report_period),
    )

    render_export_buttons(
        excel_bytes,
        "yield_by_route.xlsx",
        pdf_bytes,
        "yield_by_route.pdf",
        "yield_excel_new",
        "yield_pdf_new",
    )