from __future__ import annotations

import pandas as pd

from reports import build_programmed_revenue_outputs, get_programmed_revenue_filter_options

from .programmed_revenue_common import MESES, fmt_flight, normalize_summary_for_display


def get_programmed_revenue_ui_options(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "route_options": [],
            "year_options": [],
            "month_options": [],
            "default_route": None,
            "default_year": None,
            "default_month": None,
        }

    options = get_programmed_revenue_filter_options(df)

    route_options = options.get("routes", []) or []
    year_options = options.get("years", []) or []
    month_options = options.get("months", []) or []

    default_route = route_options[0] if route_options else None
    default_year = year_options[-1] if year_options else None
    default_month = month_options[-1] if month_options else None

    return {
        "route_options": route_options,
        "year_options": year_options,
        "month_options": month_options,
        "default_route": default_route,
        "default_year": default_year,
        "default_month": default_month,
    }


def prepare_programmed_revenue_module_outputs(
    df: pd.DataFrame,
    route: str,
    month: int,
    year: int,
) -> dict:
    outputs = build_programmed_revenue_outputs(
        df=df,
        route=route,
        month=int(month),
        year=int(year),
    )

    summary = outputs.get("summary", pd.DataFrame()).copy()
    detail = outputs.get("detail", pd.DataFrame()).copy()
    validation = outputs.get("validation", {}) or {}

    if not summary.empty:
        summary = normalize_summary_for_display(summary)

    if not detail.empty and "vuelo" in detail.columns:
        detail = detail.copy()
        detail["vuelo"] = detail["vuelo"].map(fmt_flight)

    total_ingreso = float(summary["Ingreso"].sum()) if not summary.empty and "Ingreso" in summary.columns else 0.0
    total_cupones = int(summary["Cupones"].sum()) if not summary.empty and "Cupones" in summary.columns else 0
    total_tickets = int(summary["Tickets"].sum()) if not summary.empty and "Tickets" in summary.columns else 0

    title = f"Resumen mensual — {route} — {MESES.get(month, month)} {year}"

    display_summary = pd.DataFrame()
    pdf_df = pd.DataFrame()

    if not summary.empty:
        display_summary = summary.rename(
            columns={
                "fecha_prog": "Fecha",
                "origen": "Origen",
                "destino": "Destino",
                "vuelo": "Vuelo",
                "Cupones": "Cupones",
                "Tickets": "Tickets",
                "Ingreso": "Ingreso",
                "TKTT_Ingreso": "TKTT Ingreso",
                "EMDA_Ingreso": "EMDA Ingreso",
            }
        ).copy()

        pdf_df = summary.rename(
            columns={
                "fecha_prog": "Fecha",
                "origen": "Origen",
                "destino": "Destino",
                "vuelo": "Vuelo",
                "Cupones": "Cupones",
                "Ingreso": "Ingreso",
            }
        )[["Fecha", "Origen", "Destino", "Vuelo", "Cupones", "Ingreso"]].copy()

    validation_display = {
        "TKTT_cupones_generados": validation.get("total_tktt_coupon_rows", 0),
        "EMDA_rows_asignados": validation.get("total_emda_allocated_rows", 0),
        "EMDA_sin_related_doc_match": validation.get("unmatched_emda", 0),
        "Documentos_en_filtro": validation.get("documents_in_scope", 0),
    }

    return {
        "title": title,
        "summary": summary,
        "detail": detail,
        "validation": validation,
        "validation_display": validation_display,
        "display_summary": display_summary,
        "pdf_df": pdf_df,
        "kpis": {
            "total_ingreso": total_ingreso,
            "total_cupones": total_cupones,
            "total_tickets": total_tickets,
            "unmatched_emda": int(validation.get("unmatched_emda", 0)),
        },
    }