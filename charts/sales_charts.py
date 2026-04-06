import io

import matplotlib.pyplot as plt
import plotly.express as px

from .common import ESTELAR_BLUE, base_layout


def chart_sales_by_month(monthly_df):
    if monthly_df.empty:
        return base_layout(px.bar(title="Ventas por Mes"))

    df = monthly_df.copy()
    df = df[df["Mes"].astype(str).str.upper() != "TOTAL AÑO"]
    if df.empty:
        return base_layout(px.bar(title="Ventas por Mes"))

    fig = px.bar(
        df,
        x="Mes",
        y="Revenue USD",
        text="Revenue USD",
        title="Ventas por Mes",
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Ingreso USD")
    return base_layout(fig)


def chart_sales_by_week(weekly_df, month_label=""):
    if weekly_df.empty:
        return base_layout(px.bar(title="Ventas Semanales"))

    df = weekly_df.copy()
    df = df[df["Semana"].astype(str).str.upper() != "TOTAL MES"]
    if df.empty:
        return base_layout(px.bar(title="Ventas Semanales"))

    fig = px.bar(
        df,
        x="Semana",
        y="Ingreso USD",
        text="Ingreso USD",
        title=f"Ventas Semanales - {month_label}".strip(" -"),
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        marker_color=ESTELAR_BLUE,
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Ingreso USD")
    return base_layout(fig)


def chart_sales_route_month(route_month_df, top_n=10):
    if route_month_df is None or route_month_df.empty:
        return base_layout(px.bar(title="Revenue por Ruta y Mes"))

    df = route_month_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].copy()
    if df.empty:
        return base_layout(px.bar(title="Revenue por Ruta y Mes"))

    month_cols = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]
    available_month_cols = [c for c in month_cols if c in df.columns]

    if not available_month_cols:
        return base_layout(px.bar(title="Revenue por Ruta y Mes"))

    if "TOTAL" in df.columns:
        df = df.sort_values("TOTAL", ascending=False).head(top_n).copy()
    else:
        df["TOTAL"] = df[available_month_cols].sum(axis=1)
        df = df.sort_values("TOTAL", ascending=False).head(top_n).copy()

    long_df = df.melt(
        id_vars=["Ruta"],
        value_vars=available_month_cols,
        var_name="Mes",
        value_name="Ingreso USD",
    )

    long_df = long_df[long_df["Ingreso USD"] > 0].copy()
    if long_df.empty:
        return base_layout(px.bar(title="Revenue por Ruta y Mes"))

    month_order = {m: i for i, m in enumerate(month_cols)}
    long_df["MesOrden"] = long_df["Mes"].map(month_order)
    long_df = long_df.sort_values(["MesOrden", "Ingreso USD"], ascending=[True, False])

    fig = px.bar(
        long_df,
        x="Mes",
        y="Ingreso USD",
        color="Ruta",
        barmode="group",
        title=f"Revenue por Ruta y Mes - Top {min(top_n, df['Ruta'].nunique())} rutas",
    )
    fig.update_xaxes(
        title="",
        categoryorder="array",
        categoryarray=month_cols,
    )
    fig.update_yaxes(title="Ingreso USD")
    return base_layout(fig)


def build_sales_route_month_chart_png(route_month_df, top_n=10):
    if route_month_df is None or route_month_df.empty:
        return None

    df = route_month_df.copy()
    df = df[df["Ruta"].astype(str).str.upper() != "TOTAL"].copy()
    if df.empty:
        return None

    month_cols = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]
    available_month_cols = [c for c in month_cols if c in df.columns]

    if not available_month_cols:
        return None

    if "TOTAL" in df.columns:
        df = df.sort_values("TOTAL", ascending=False).head(top_n).copy()
    else:
        df["TOTAL"] = df[available_month_cols].sum(axis=1)
        df = df.sort_values("TOTAL", ascending=False).head(top_n).copy()

    if df.empty:
        return None

    x = list(range(len(available_month_cols)))
    n_routes = len(df)
    width = 0.8 / max(n_routes, 1)

    fig, ax = plt.subplots(figsize=(14, 6))

    for idx, (_, row) in enumerate(df.iterrows()):
        y = [float(row[col]) for col in available_month_cols]
        offset = (idx - (n_routes - 1) / 2) * width
        ax.bar(
            [v + offset for v in x],
            y,
            width=width,
            label=str(row["Ruta"]),
        )

    ax.set_title(
        f"Revenue por Ruta y Mes - Top {min(top_n, len(df))} rutas",
        fontsize=16,
        fontweight="bold",
    )
    ax.set_xlabel("Mes", fontsize=11, fontweight="bold")
    ax.set_ylabel("Ingreso USD", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(available_month_cols, rotation=35, ha="right")

    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D9E2EF")
    ax.spines["bottom"].set_color("#D9E2EF")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()