import streamlit as st


APP_CSS = """
<style>
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 1rem;
    max-width: 1500px;
}

div[data-testid="stMetric"] {
    background: #f7f9fc;
    border: 1px solid #dde6f0;
    padding: 14px;
    border-radius: 14px;
}

.header-wrap {
    text-align: center;
    margin-top: 0.1rem;
    margin-bottom: 0.4rem;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #162f6b;
    margin-top: 0.1rem;
    margin-bottom: 0.1rem;
    text-align: center;
}

.subtitle {
    color: #5d6677;
    margin-bottom: 0.2rem;
    font-size: 1rem;
    text-align: center;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-top: 0.2rem;
    margin-bottom: 0.7rem;
}

.module-filter-wrap {
    background: #f7f9fc;
    border: 1px solid #dde6f0;
    padding: 14px 16px;
    border-radius: 14px;
    margin-bottom: 16px;
}

.sidebar-logo-wrap {
    text-align: center;
    padding-top: 0.6rem;
    padding-bottom: 1rem;
}

.sidebar-logo-wrap img {
    width: 100%;
    max-width: 320px;
    height: auto;
    display: block;
    margin: 0 auto;
}

section[data-testid="stSidebar"] {
    background: #f4f7fb;
    border-right: 1px solid #dde6f0;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.sidebar-section {
    margin-top: 1.1rem;
    margin-bottom: 0.55rem;
    font-size: 0.82rem;
    font-weight: 800;
    color: #687385;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
    font-size: 0.95rem;
    font-weight: 600;
    color: #394150;
    margin-bottom: 0.35rem;
}

div[role="radiogroup"] {
    gap: 0.45rem;
}

div[role="radiogroup"] > label {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    min-height: 52px;
    padding: 0.75rem 0.95rem;
    border-radius: 14px;
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.18s ease;
    cursor: pointer;
    margin: 0;
}

div[role="radiogroup"] > label:hover {
    background: #e9f0fb;
    border-color: #d7e2f2;
}

div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

div[role="radiogroup"] > label > div:last-child {
    width: 100%;
}

div[role="radiogroup"] > label p {
    margin: 0 !important;
    font-size: 1rem;
    font-weight: 600;
    color: #2f3542 !important;
    line-height: 1.2;
}

div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, #162f6b 0%, #1d3f8a 100%);
    border-color: #162f6b;
    box-shadow: 0 8px 20px rgba(22, 47, 107, 0.18);
}

div[role="radiogroup"] > label:has(input:checked) p {
    color: #ffffff !important;
    font-weight: 700;
}

div[role="radiogroup"] > label:has(input:checked):hover {
    background: linear-gradient(135deg, #162f6b 0%, #1d3f8a 100%);
    border-color: #162f6b;
}
</style>
"""


def apply_app_styles():
    st.markdown(APP_CSS, unsafe_allow_html=True)