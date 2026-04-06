from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from db_data_loader import load_programmed_revenue_source
from reports import build_volado_by_route_report


def _safe_kpis(report_df: pd.DataFrame) -> dict:
    if report_df is None or report_df.empty:
        return {
            "total_revenue": 0.0,
            "total_coupons": 0,
            "total_routes": 0,
        }

    work = report_df.copy()
    if "Ruta" in work.columns:
        work = work[work["Ruta"].astype(str).str.upper() != "TOTAL"].copy()

    total_revenue = float(pd.to_numeric(work.get("Ingreso USD", 0), errors="coerce").fillna(0).sum())
    total_coupons = int(pd.to_numeric(work.get("Cupones", 0), errors="coerce").fillna(0).sum())
    total_routes = int(work["Ruta"].astype(str).nunique()) if "Ruta" in work.columns and not work.empty else 0

    return {
        "total_revenue": total_revenue,
        "total_coupons": total_coupons,
        "total_routes": total_routes,
    }


def prepare_volado_outputs(date_from: Any = None, date_to: Any = None) -> dict:
    raw_df = load_programmed_revenue_source()

    if raw_df is None:
        raw_df = pd.DataFrame()

    volado_df = build_volado_by_route_report(
        raw_df,
        date_from=date_from,
        date_to=date_to,
    )

    kpis = _safe_kpis(volado_df)

    return {
        "volado_df": volado_df,
        "kpis": kpis,
    }