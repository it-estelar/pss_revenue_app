import math

import pandas as pd
import streamlit as st

from .formatters import format_int_es, format_money_es, format_number_es


def _looks_numeric(series: pd.Series) -> bool:
    if series.empty:
        return False
    converted = pd.to_numeric(series, errors="coerce")
    return converted.notna().sum() >= max(1, int(len(series) * 0.7))


def _is_money_column(col_name: str) -> bool:
    name = str(col_name).strip().lower()
    money_keywords = [
        "revenue",
        "ingreso",
        "usd",
        "monto",
        "yield",
        "venta",
        "tarifa",
        "valor",
    ]
    return any(k in name for k in money_keywords)


def _is_count_column(col_name: str) -> bool:
    name = str(col_name).strip().lower()
    count_keywords = [
        "cantidad",
        "cupones",
        "coupon",
        "tickets",
        "tktt",
        "emda",
        "emds",
        "#",
    ]
    return any(k in name for k in count_keywords)


def _format_dataframe_for_display(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame.copy()

    df = frame.copy()

    for col in df.columns:
        if _looks_numeric(df[col]):
            numeric_col = pd.to_numeric(df[col], errors="coerce")

            if _is_money_column(col):
                df[col] = numeric_col.map(
                    lambda x: format_money_es(x, decimals=2) if pd.notna(x) else ""
                )
            elif _is_count_column(col):
                df[col] = numeric_col.map(
                    lambda x: format_int_es(x) if pd.notna(x) else ""
                )
            else:
                has_decimals = (
                    ((numeric_col.dropna() % 1) != 0).any()
                    if not numeric_col.dropna().empty
                    else False
                )
                if has_decimals:
                    df[col] = numeric_col.map(
                        lambda x: format_number_es(x, decimals=2) if pd.notna(x) else ""
                    )
                else:
                    df[col] = numeric_col.map(
                        lambda x: format_int_es(x) if pd.notna(x) else ""
                    )

    return df


def _table_css(style_name: str) -> str:
    if style_name == "Executive Blue":
        return """
        <style>
        .report-table-wrap table {
            width: 100%;
            border-collapse: collapse;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 14px;
            border: 1px solid #d9e2ef;
            border-radius: 12px;
            overflow: hidden;
        }
        .report-table-wrap thead th {
            background: #162f6b;
            color: #ffffff;
            font-weight: 700;
            text-align: left;
            padding: 10px 12px;
            border: 1px solid #d9e2ef;
        }
        .report-table-wrap tbody td {
            padding: 9px 12px;
            border: 1px solid #e3eaf3;
            color: #24364a;
        }
        .report-table-wrap tbody tr:nth-child(even) {
            background: #f7f9fc;
        }
        .report-table-wrap tbody tr:hover {
            background: #eef4ff;
        }
        </style>
        """

    if style_name == "Soft Gray":
        return """
        <style>
        .report-table-wrap table {
            width: 100%;
            border-collapse: collapse;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 14px;
            border: 1px solid #dde3ea;
            border-radius: 12px;
            overflow: hidden;
        }
        .report-table-wrap thead th {
            background: #eef2f7;
            color: #22324a;
            font-weight: 700;
            text-align: left;
            padding: 10px 12px;
            border: 1px solid #d8e0e8;
        }
        .report-table-wrap tbody td {
            padding: 9px 12px;
            border: 1px solid #e8edf3;
            color: #2b3a4f;
        }
        .report-table-wrap tbody tr:nth-child(even) {
            background: #fafbfd;
        }
        .report-table-wrap tbody tr:hover {
            background: #f2f5f9;
        }
        </style>
        """

    return """
    <style>
    .report-table-wrap table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        font-size: 14px;
        border: 1px solid #e1e5ea;
    }
    .report-table-wrap thead th {
        background: #f5f6f8;
        color: #222;
        font-weight: 700;
        text-align: left;
        padding: 9px 10px;
        border: 1px solid #e1e5ea;
    }
    .report-table-wrap tbody td {
        padding: 8px 10px;
        border: 1px solid #eceff3;
        color: #222;
    }
    .report-table-wrap tbody tr:nth-child(even) {
        background: #fbfbfc;
    }
    </style>
    """


def render_table(frame: pd.DataFrame, style_name: str, key_suffix: str):
    if frame is None or frame.empty:
        st.info("No hay datos para mostrar.")
        return

    display_df = _format_dataframe_for_display(frame)

    html = display_df.to_html(index=False, escape=False)
    st.markdown(_table_css(style_name), unsafe_allow_html=True)
    st.markdown(
        f'<div class="report-table-wrap" id="table_{key_suffix}">{html}</div>',
        unsafe_allow_html=True,
    )


def render_paginated_table(
    frame: pd.DataFrame,
    style_name: str,
    key_suffix: str,
    *,
    rows_per_page_options=(10, 25, 50, 100),
    default_rows_per_page=25,
):
    if frame is None or frame.empty:
        st.info("No hay datos para mostrar.")
        return

    total_rows = len(frame)
    display_df = _format_dataframe_for_display(frame)

    if default_rows_per_page not in rows_per_page_options:
        rows_per_page_options = tuple(
            sorted(set(rows_per_page_options + (default_rows_per_page,)))
        )

    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        rows_per_page = st.selectbox(
            "Filas por página",
            options=list(rows_per_page_options),
            index=list(rows_per_page_options).index(default_rows_per_page),
            key=f"{key_suffix}_rows_per_page",
        )

    total_pages = max(1, math.ceil(total_rows / rows_per_page))

    with c2:
        page_number = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"{key_suffix}_page_number",
        )

    start_idx = (page_number - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)

    with c3:
        st.markdown(
            f"<div style='padding-top: 30px;'>Mostrando {start_idx + 1}-{end_idx} de {total_rows} filas</div>",
            unsafe_allow_html=True,
        )

    page_df = display_df.iloc[start_idx:end_idx].copy()

    html = page_df.to_html(index=False, escape=False)
    st.markdown(_table_css(style_name), unsafe_allow_html=True)
    st.markdown(
        f'<div class="report-table-wrap" id="table_{key_suffix}">{html}</div>',
        unsafe_allow_html=True,
    )