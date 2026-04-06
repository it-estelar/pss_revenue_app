import streamlit as st

from ui import metric_text_int, metric_text_money


def safe_unique_sorted(series):
    vals = [str(x).strip() for x in series.astype(str).tolist() if str(x).strip()]
    return sorted(set(vals))


def show_header():
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-title">Estelar Revenue Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Revenue, yield, routes and issuer analysis</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()


def show_kpis(kpis):
    st.markdown('<div class="section-title">Resumen General</div>', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    k1.metric("Revenue Total", metric_text_money(kpis.get("total_revenue", 0)))
    k2.metric("Cupones Totales", metric_text_int(kpis.get("total_coupons", 0)))
    k3.metric("Tickets Únicos", metric_text_int(kpis.get("unique_tickets", 0)))


def build_report_period(date_from=None, date_to=None):
    if date_from and date_to:
        return f"Período: {date_from} a {date_to}"
    if date_from:
        return f"Período: desde {date_from}"
    if date_to:
        return f"Período: hasta {date_to}"
    return "Período: todo el histórico disponible"