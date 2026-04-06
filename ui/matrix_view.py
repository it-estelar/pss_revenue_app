from __future__ import annotations

import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from charts import chart_emisor_route_matrix
from exporters import build_single_table_pdf
from services import get_available_reference_years, prepare_route_matrix_outputs

from .shared import build_pdf_subtitle, render_section_title


def _safe_year_options(coupons_long):
    years = get_available_reference_years(coupons_long)
    return years if years else []


def _build_heatmap_chart_png(heatmap_df: pd.DataFrame, title: str | None = None):
    if heatmap_df is None or heatmap_df.empty:
        return None

    heat = heatmap_df.copy()

    if "Mes/Año Programado" in heat.columns:
        heat = heat.set_index("Mes/Año Programado")

    if heat.empty or len(heat.columns) == 0:
        return None

    heat = heat.apply(pd.to_numeric, errors="coerce").fillna(0)

    values = heat.to_numpy(dtype=float)
    masked = np.ma.masked_where(values <= 0, values)

    fig, ax = plt.subplots(figsize=(13.5, 6.6))

    cmap = plt.cm.Blues.copy()
    cmap.set_bad(color="white")

    im = ax.imshow(masked, aspect="auto", cmap=cmap)

    chart_title = title or "Heatmap de Compra vs Programación"
    ax.set_title(
        chart_title,
        fontsize=18,
        fontweight="bold",
        color="#16324F",
        pad=16,
    )

    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels(heat.columns, rotation=45, ha="right", fontsize=10, color="#44506A")

    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index, fontsize=10, color="#44506A")

    ax.set_xlabel(
        "Mes/Año de Compra del Boleto",
        fontsize=12,
        fontweight="bold",
        color="#16324F",
        labelpad=14,
    )
    ax.set_ylabel(
        "Mes/Año de Programación del Vuelo",
        fontsize=12,
        fontweight="bold",
        color="#16324F",
        labelpad=16,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", which="both", length=0)

    max_val = float(values.max()) if values.size else 0.0
    threshold = max_val * 0.55 if max_val > 0 else 0.0

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            val = values[i, j]
            if val > 0:
                txt_color = "white" if val >= threshold else "#16324F"
                ax.text(
                    j,
                    i,
                    f"{int(round(val))}",
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold" if val >= threshold else "normal",
                    color=txt_color,
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.03)
    cbar.ax.set_title("Cupones", fontsize=10, color="#16324F", pad=8)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(labelsize=9, colors="#44506A")

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _build_export_table_df(heatmap_df: pd.DataFrame) -> pd.DataFrame:
    if heatmap_df is None or heatmap_df.empty:
        return pd.DataFrame(columns=["Mes/Año Programado"])

    export_df = heatmap_df.reset_index().rename(columns={"index": "Mes/Año Programado"})
    return export_df


def render_route_matrix(coupons_long, route_options):
    render_section_title("Heatmap de Compra vs Programación")

    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            padding: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if coupons_long is None or coupons_long.empty:
        st.warning("No hay datos de cupones disponibles para este módulo.")
        return

    if not route_options:
        st.warning("No hay rutas disponibles.")
        return

    year_options = _safe_year_options(coupons_long)
    if not year_options:
        st.warning("No hay años programados disponibles.")
        return

    if "route_matrix_generated" not in st.session_state:
        st.session_state["route_matrix_generated"] = False

    if "route_matrix_selected_route" not in st.session_state:
        st.session_state["route_matrix_selected_route"] = route_options[0]

    if "route_matrix_selected_year" not in st.session_state:
        st.session_state["route_matrix_selected_year"] = max(year_options)

    with st.form("route_matrix_form", clear_on_submit=False):
        st.markdown("## Parámetros del Reporte")

        c1, c2 = st.columns(2)

        with c1:
            st.selectbox(
                "Ruta",
                options=route_options,
                key="route_matrix_selected_route",
            )

        with c2:
            st.selectbox(
                "Año de Referencia",
                options=year_options,
                key="route_matrix_selected_year",
                help="Año base del vuelo programado. Si eliges 2026, se incluyen boletos vendidos en 2025 para volar en 2026.",
            )

        submitted = st.form_submit_button(
            "Generar Heatmap",
            use_container_width=True,
        )

        if submitted:
            st.session_state["route_matrix_generated"] = True

    if not st.session_state.get("route_matrix_generated", False):
        st.info("Selecciona la ruta y el año programado, luego pulsa Generar Heatmap.")
        return

    selected_route = st.session_state["route_matrix_selected_route"]
    selected_year = int(st.session_state["route_matrix_selected_year"])

    prepared = prepare_route_matrix_outputs(
        coupons_long,
        selected_route,
        selected_year,
    )

    heatmap_df = prepared["heatmap_df"]
    kpis = prepared["kpis"]
    subtitle = prepared["subtitle"]

    if heatmap_df.empty:
        st.warning("No hay cupones para la ruta y el año programado seleccionados.")
        return

    st.caption("Los períodos están ordenados cronológicamente en ambos ejes.")
    st.markdown(f"**{subtitle}**")

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Cupones", f"{kpis['total_coupons']:,}")
    with k2:
        st.metric("Meses compra", f"{kpis['purchase_months']:,}")
    with k3:
        st.metric("Meses programados", f"{kpis['programmed_months']:,}")

    st.markdown("")

    fig = chart_emisor_route_matrix(heatmap_df)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displaylogo": False},
    )

    chart_png = _build_heatmap_chart_png(
        heatmap_df,
        title="Heatmap de Compra vs Programación",
    )

    pdf_df = _build_export_table_df(heatmap_df)

    pdf_subtitle = build_pdf_subtitle(
        "Cantidad de cupones vendidos por mes/año de compra frente al mes/año programado del vuelo.",
        f"Ruta: {selected_route} | Año programado: {selected_year}",
    )

    pdf_bytes = build_single_table_pdf(
        title="Heatmap de Compra vs Programación",
        df=pdf_df,
        styled=True,
        subtitle=pdf_subtitle,
        chart_png=chart_png,
        kpi_pairs=[
            ("Ruta", selected_route),
            ("Año programado", str(selected_year)),
            ("Cupones", f"{int(kpis['total_coupons']):,}"),
        ],
        chart_first_page=True,
    )

    st.download_button(
        "Exportar gráfico a PDF",
        data=pdf_bytes,
        file_name=f"heatmap_compra_vs_programacion_{selected_route}_{selected_year}.pdf",
        mime="application/pdf",
        key="download_heatmap_pdf",
    )