import io

import matplotlib.pyplot as plt
import plotly.express as px

from .common import ESTELAR_BLUE, base_layout


def chart_route_class_mix(route_class_df, route_name="", top_n=10):
    if route_class_df.empty:
        return base_layout(px.bar(title="Mix de Clases"))

    df = route_class_df.copy()
    df = df[df["Clase"].astype(str).str.upper() != "TOTAL"].head(top_n)

    fig = px.bar(
        df,
        x="Clase",
        y="Cantidad_de_Cupones",
        text="Cantidad_de_Cupones",
        title=f"Top Clases Vendidas - {route_name}".strip(" -"),
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Cantidad de Cupones")
    return base_layout(fig)


def build_route_class_chart_png(route_class_df, route_name="", top_n=10):
    if route_class_df is None or route_class_df.empty:
        return None

    df = route_class_df.copy()
    df = df[df["Clase"].astype(str).str.upper() != "TOTAL"].head(top_n)

    if df.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(
        df["Clase"].astype(str),
        df["Cantidad_de_Cupones"].astype(float),
        color="#2c7bb6",
        edgecolor="#0f2f6f",
        linewidth=1.2,
    )

    ax.set_title(
        f"Top Clases Vendidas - {route_name}",
        fontsize=18,
        fontweight="bold",
        color="#16324F",
        pad=14,
    )
    ax.set_xlabel("Clase", fontsize=12, fontweight="bold", color="#16324F")
    ax.set_ylabel("Cantidad de Cupones", fontsize=12, fontweight="bold", color="#16324F")

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D9E2EF")
    ax.spines["bottom"].set_color("#D9E2EF")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    max_value = float(df["Cantidad_de_Cupones"].max()) if not df.empty else 0

    for bar, value in zip(bars, df["Cantidad_de_Cupones"].astype(int)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(max_value * 0.015, 3),
            f"{value:,}".replace(",", "."),
            ha="center",
            va="bottom",
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