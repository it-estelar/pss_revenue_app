import pandas as pd
import plotly.express as px

from .common import base_layout


def chart_emisor_route_matrix(matrix_df):
    if matrix_df is None or matrix_df.empty:
        fig = px.imshow([[0]])
        fig.update_layout(
            title=dict(
                text="Heatmap de Compra vs Programación",
                x=0.5,
                xanchor="center",
                font=dict(size=22),
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        return base_layout(fig)

    heat = matrix_df.copy()

    if "Mes/Año Programado" in heat.columns:
        heat = heat.set_index("Mes/Año Programado")

    heat = heat.apply(pd.to_numeric, errors="coerce").fillna(0)

    # Oculta visualmente los ceros
    heat_for_color = heat.mask(heat <= 0)

    fig = px.imshow(
        heat_for_color,
        aspect="auto",
        text_auto=True,
        color_continuous_scale=[
            [0.00, "#EAF1FB"],
            [0.20, "#C9DAF3"],
            [0.40, "#9FBFE8"],
            [0.60, "#6F9BD7"],
            [0.80, "#355FAD"],
            [1.00, "#1E3A78"],
        ],
    )

    fig.update_traces(
        hovertemplate=(
            "Programado: %{y}<br>"
            "Compra: %{x}<br>"
            "Cupones: %{z}<extra></extra>"
        )
    )

    fig.update_xaxes(
        title="Mes/Año de Compra del Boleto",
        tickangle=-45,
        showgrid=False,
        zeroline=False,
        showline=False,
    )

    fig.update_yaxes(
        title="Mes/Año de Programación del Vuelo",
        showgrid=False,
        zeroline=False,
        showline=False,
    )

    fig.update_layout(
        height=700,
        title=dict(
            text="Heatmap de Compra vs Programación",
            x=0.5,
            xanchor="center",
            font=dict(size=22, color="#203864"),
        ),
        coloraxis_colorbar=dict(
            title="Cupones",
            thickness=16,
        ),
        margin=dict(l=50, r=20, t=85, b=120),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return base_layout(fig)