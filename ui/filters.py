from typing import Any

import streamlit as st


def normalize_date_input(value: Any):
    if isinstance(value, tuple):
        return value[0] if value else None
    return value


def render_module_date_filters(module_key: str):
    st.markdown('<div class="module-filter-wrap">', unsafe_allow_html=True)
    st.markdown("#### Filtros del módulo")

    c1, c2 = st.columns(2)
    with c1:
        date_from = st.date_input(
            "Desde",
            value=None,
            key=f"{module_key}_date_from",
        )
    with c2:
        date_to = st.date_input(
            "Hasta",
            value=None,
            key=f"{module_key}_date_to",
        )

    date_from = normalize_date_input(date_from)
    date_to = normalize_date_input(date_to)

    if date_from and date_to and date_from > date_to:
        st.error("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    st.markdown("</div>", unsafe_allow_html=True)
    return date_from, date_to