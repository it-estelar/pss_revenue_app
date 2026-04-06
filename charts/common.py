ESTELAR_BLUE = "#162f6b"
ESTELAR_LIGHT = "#d9e4f5"


def base_layout(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        title_x=0.5,
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=430,
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
    )

    return fig