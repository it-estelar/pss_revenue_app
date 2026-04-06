import io

import matplotlib.pyplot as plt
import plotly.express as px

from .common import ESTELAR_BLUE, base_layout


def chart_top_emisores(report_df, top_n=10):
    if report_df is None or report_df.empty:
        return base_layout(px.bar(title="Top Emisores"))

    df = report_df.copy()
    df = df[df["Emisor"].astype(str).str.upper() != "TOTAL"].head(top_n)

    fig = px.bar(
        df,
        x="Revenue",
        y="Emisor",
        orientation="h",
        text="Revenue",
        title=f"Top {top_n} Emisores",
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return base_layout(fig)


def chart_top_routes(report_df, top_n=10):
    if report_df is None or report_df.empty:
        return base_layout(px.bar(title="Top Rutas"))

    df = report_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].head(top_n)

    fig = px.bar(
        df,
        x="Revenue",
        y="Ruta",
        orientation="h",
        text="Revenue",
        title=f"Top {top_n} Rutas por Revenue",
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return base_layout(fig)


def build_top_routes_chart_png(report_df, top_n=10, title=None):
    if report_df is None or report_df.empty:
        return None

    df = report_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].copy()
    df = df.head(top_n)

    if df.empty:
        return None

    df = df.sort_values("Revenue", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(13, 6))

    bars = ax.barh(
        df["Ruta"].astype(str),
        df["Revenue"].astype(float),
        color="#1f4e79",
        edgecolor="#0f2f6f",
        linewidth=1.1,
    )

    chart_title = title or f"Top {min(top_n, len(df))} rutas por revenue"
    ax.set_title(
        chart_title,
        fontsize=18,
        fontweight="bold",
        color="#16324F",
        pad=14,
    )
    ax.set_xlabel("Revenue USD", fontsize=12, fontweight="bold", color="#16324F")
    ax.set_ylabel("Ruta", fontsize=12, fontweight="bold", color="#16324F")

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D9E2EF")
    ax.spines["bottom"].set_color("#D9E2EF")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    max_value = float(df["Revenue"].max()) if not df.empty else 0

    for bar, value in zip(bars, df["Revenue"].astype(float)):
        ax.text(
            bar.get_width() + max(max_value * 0.012, 250),
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.0f}",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#16324F",
        )

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def chart_yield_by_route(report_df, top_n=10):
    if report_df is None or report_df.empty:
        return base_layout(px.bar(title="Yield por Ruta"))

    df = report_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].head(top_n)

    fig = px.bar(
        df,
        x="Yield",
        y="Ruta",
        orientation="h",
        text="Yield",
        title=f"Top {top_n} Rutas por Yield",
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return base_layout(fig)


def chart_volado_by_route(report_df, top_n=10):
    if report_df is None or report_df.empty:
        return base_layout(px.bar(title="Volado por Ruta"))

    df = report_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].head(top_n)

    fig = px.bar(
        df,
        x="Ingreso USD",
        y="Ruta",
        orientation="h",
        text="Ingreso USD",
        title=f"Top {top_n} rutas por revenue programado",
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return base_layout(fig)


def build_volado_chart_png(report_df, top_n=10):
    if report_df is None or report_df.empty:
        return None

    df = report_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].head(top_n).copy()

    if df.empty:
        return None

    df = df.sort_values("Ingreso USD", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 6))
    bars = ax.barh(df["Ruta"], df["Ingreso USD"], color="#1f4e79")

    ax.set_title(f"Top {min(top_n, len(df))} rutas por revenue programado")
    ax.set_xlabel("Ingreso USD")
    ax.set_ylabel("Ruta")

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D9E2EF")
    ax.spines["bottom"].set_color("#D9E2EF")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    max_value = float(df["Ingreso USD"].max()) if not df.empty else 0
    for bar, value in zip(bars, df["Ingreso USD"].astype(float)):
        ax.text(
            bar.get_width() + max(max_value * 0.012, 250),
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.0f}",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#16324F",
        )

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()