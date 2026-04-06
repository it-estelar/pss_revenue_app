import streamlit as st

from charts import build_volado_chart_png, chart_volado_by_route
from exporters import build_single_table_pdf, single_df_to_excel_bytes

from .shared import build_pdf_subtitle, render_export_buttons, render_table


def render_volado_module(volado_df, top_n, show_tables, report_period=None):
    st.markdown('<div class="section-title">Volado</div>', unsafe_allow_html=True)

    if volado_df is None or volado_df.empty:
        st.warning("No hay revenue programado por ruta para el rango seleccionado.")
        return

    st.plotly_chart(
        chart_volado_by_route(volado_df, top_n=top_n),
        use_container_width=True,
        config={"displaylogo": False},
    )

    table_style = "Executive Blue"

    if show_tables:
        table_style = st.selectbox(
            "Estilo de tabla",
            ["Standard", "Executive Blue", "Soft Gray"],
            index=1,
            key="volado_table_style",
        )
        render_table(volado_df, table_style, "volado_by_route")

    excel_bytes = single_df_to_excel_bytes(volado_df, "volado_by_route")
    chart_png = build_volado_chart_png(volado_df, top_n=top_n)

    pdf_bytes = build_single_table_pdf(
        title="Volado - Programmed Revenue by Route",
        df=volado_df,
        styled=True,
        max_rows=5000,
        subtitle=build_pdf_subtitle(
            "Revenue programado agrupado por ruta según la fecha programada de vuelo.",
            report_period,
        ),
        chart_png=chart_png,
        chart_first_page=True,
        kpi_pairs=[
            ("Revenue total", f"{float(volado_df.loc[volado_df['Ruta'] != 'TOTAL', 'Ingreso USD'].sum()):,.0f} USD"),
            ("Cupones", f"{int(volado_df.loc[volado_df['Ruta'] != 'TOTAL', 'Cupones'].sum()):,}"),
            ("Tickets", f"{int(volado_df.loc[volado_df['Ruta'] != 'TOTAL', 'Tickets'].sum()):,}"),
        ],
    )

    render_export_buttons(
        excel_bytes,
        "volado_by_route.xlsx",
        pdf_bytes,
        "volado_by_route.pdf",
        "volado_excel",
        "volado_pdf",
    )