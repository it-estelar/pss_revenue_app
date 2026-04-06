import streamlit as st

from .export_controls import build_pdf_subtitle, render_export_buttons
from .filters import normalize_date_input, render_module_date_filters
from .formatters import (
    format_int_es,
    format_money_es,
    format_number_es,
    metric_text_int,
    metric_text_money,
    metric_text_number,
)
from .tables import render_paginated_table, render_table


TABLE_STYLE_OPTIONS = ["Executive Blue", "Soft Gray", "Standard"]


def render_section_title(title: str, level: str = "section"):
    if level == "section":
        st.markdown(
            f'<div class="section-title">{title}</div>',
            unsafe_allow_html=True,
        )
    elif level == "subsection":
        st.markdown(f"#### {title}")
    else:
        st.markdown(f"**{title}**")


def select_table_style(
    key: str,
    default: str = "Executive Blue",
    *,
    label: str = "Estilo de tabla",
    help_text: str | None = None,
):
    options = TABLE_STYLE_OPTIONS[:]
    index = options.index(default) if default in options else 0
    return st.selectbox(
        label,
        options,
        index=index,
        key=key,
        help=help_text,
    )


def render_report_period(report_period: str | None):
    if report_period:
        st.markdown(f"**{report_period}**")


def render_selection_summary(
    label: str,
    items,
    *,
    empty_text: str | None = None,
    use_caption_for_values: bool = True,
):
    items = list(items or [])
    if items:
        st.markdown(f"**{label}:** {len(items)}")
        if use_caption_for_values:
            st.caption(", ".join(map(str, items)))
        else:
            st.markdown(", ".join(map(str, items)))
    elif empty_text:
        st.caption(empty_text)


def render_block_title(title: str, caption: str | None = None):
    st.markdown(f"#### {title}")
    if caption:
        st.caption(caption)


__all__ = [
    "format_number_es",
    "format_int_es",
    "format_money_es",
    "metric_text_number",
    "metric_text_int",
    "metric_text_money",
    "normalize_date_input",
    "render_module_date_filters",
    "render_table",
    "render_paginated_table",
    "build_pdf_subtitle",
    "render_export_buttons",
    "TABLE_STYLE_OPTIONS",
    "render_section_title",
    "select_table_style",
    "render_report_period",
    "render_selection_summary",
    "render_block_title",
]
