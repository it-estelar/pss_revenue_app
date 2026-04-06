import pandas as pd
import plotly.express as px

from .common import base_layout


def chart_user_revenue(summary_df: pd.DataFrame):
    if summary_df is None or summary_df.empty:
        fig = px.bar(title="Revenue por Usuario")
        return base_layout(fig)

    fig = px.bar(
        summary_df,
        x="USUARIO",
        y="REVENUE",
        hover_data=["TICKETS", "CUPONES", "AGENTE", "ESTACION"],
        title="Revenue por Usuario",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Revenue")
    fig.update_layout(height=480)
    return base_layout(fig)


def chart_user_monthly(monthly_df: pd.DataFrame):
    if monthly_df is None or monthly_df.empty:
        fig = px.line(title="Revenue Mensual por Usuario")
        return base_layout(fig)

    fig = px.line(
        monthly_df,
        x="MES",
        y="REVENUE",
        color="USUARIO",
        markers=True,
        title="Revenue Mensual por Usuario",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Revenue")
    fig.update_layout(height=480)
    return base_layout(fig)


def chart_user_emisor(emisor_df: pd.DataFrame):
    if emisor_df is None or emisor_df.empty:
        fig = px.bar(title="Top Emisores del Usuario")
        return base_layout(fig)

    fig = px.bar(
        emisor_df,
        x="EMISOR",
        y="REVENUE",
        hover_data=["TICKETS", "CUPONES"],
        title="Top Emisores",
    )
    fig.update_xaxes(title="", tickangle=-35)
    fig.update_yaxes(title="Revenue")
    fig.update_layout(height=480)
    return base_layout(fig)