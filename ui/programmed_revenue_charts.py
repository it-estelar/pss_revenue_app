from __future__ import annotations

import io

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st


def render_programmed_revenue_summary_chart(summary: pd.DataFrame):
    if summary is None or summary.empty:
        return

    chart_df = summary.copy()
    chart_df["Etiqueta"] = (
        chart_df["fecha_prog"].astype(str)
        + " | "
        + chart_df["origen"].astype(str)
        + "-"
        + chart_df["destino"].astype(str)
        + " | "
        + chart_df["vuelo"].astype(str)
    )

    chart_df = chart_df.sort_values("Ingreso", ascending=False).reset_index(drop=True)

    fig = px.bar(
        chart_df,
        x="Etiqueta",
        y="Ingreso",
        hover_data=["Cupones", "Tickets", "TKTT_Ingreso", "EMDA_Ingreso"],
        title="Ingreso programado por vuelo",
    )
    fig.update_layout(xaxis_title="", yaxis_title="Ingreso")
    st.plotly_chart(fig, use_container_width=True)


def build_programmed_revenue_summary_chart_png(summary: pd.DataFrame, top_n: int = 5):
    if summary is None or summary.empty:
        return None

    chart_df = summary.copy()

    if "Ingreso" not in chart_df.columns:
        return None

    chart_df["Etiqueta"] = (
        chart_df["fecha_prog"].astype(str)
        + " | "
        + chart_df["origen"].astype(str)
        + "-"
        + chart_df["destino"].astype(str)
        + " | "
        + chart_df["vuelo"].astype(str)
    )

    chart_df = (
        chart_df.sort_values("Ingreso", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    fig, ax = plt.subplots(figsize=(13.5, 6))
    ax.bar(chart_df["Etiqueta"], chart_df["Ingreso"], color="#1f4e79")
    ax.set_title(f"Top {top_n} vuelos por ingreso programado")
    ax.set_xlabel("")
    ax.set_ylabel("Ingreso USD")
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_flight_detail_charts(sub: pd.DataFrame, label: str):
    if sub is None or sub.empty:
        return

    class_df = sub.copy()
    class_df["clase"] = class_df["clase"].fillna("").astype(str).str.strip().str.upper()
    class_df = class_df[class_df["clase"] != ""].copy()

    if not class_df.empty:
        class_chart = (
            class_df.groupby("clase", dropna=False)
            .agg(Cupones=("ticket", "count"))
            .reset_index()
            .sort_values("Cupones", ascending=False)
        )
        fig_class = px.bar(
            class_chart,
            x="clase",
            y="Cupones",
            title=f"Cupones por clase — {label}",
        )
        fig_class.update_layout(xaxis_title="Clase", yaxis_title="Cupones")
        st.plotly_chart(fig_class, use_container_width=True)

    emisor_df = sub.copy()
    emisor_df["emisor"] = emisor_df["emisor"].fillna("").astype(str).str.strip()
    emisor_df = emisor_df[emisor_df["emisor"] != ""].copy()

    if not emisor_df.empty:
        emisor_chart = (
            emisor_df.groupby("emisor", dropna=False)
            .agg(Ingreso=("assigned_revenue", "sum"))
            .reset_index()
            .sort_values("Ingreso", ascending=False)
        )
        fig_emisor = px.bar(
            emisor_chart,
            x="emisor",
            y="Ingreso",
            title=f"Ingreso por emisor — {label}",
        )
        fig_emisor.update_layout(xaxis_title="Emisor", yaxis_title="Ingreso")
        st.plotly_chart(fig_emisor, use_container_width=True)