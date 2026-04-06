import streamlit as st

from charts import (
    chart_currency_class_mix,
    chart_top_emisores,
    chart_top_routes,
    chart_yield_by_route,
)


def render_dashboard(
    revenue_by_emisor_df,
    yield_by_route_df,
    routes_for_chart,
    revenue_by_currency_class_df,
    top_n,
):
    st.markdown('<div class="section-title">Dashboard Ejecutivo</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            chart_top_emisores(revenue_by_emisor_df, top_n=top_n),
            use_container_width=True,
            config={"displaylogo": False},
        )
    with c2:
        st.plotly_chart(
            chart_yield_by_route(yield_by_route_df, top_n=top_n),
            use_container_width=True,
            config={"displaylogo": False},
        )

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(
            chart_top_routes(routes_for_chart, top_n=top_n),
            use_container_width=True,
            config={"displaylogo": False},
        )
    with c4:
        st.plotly_chart(
            chart_currency_class_mix(revenue_by_currency_class_df, None),
            use_container_width=True,
            config={"displaylogo": False},
        )