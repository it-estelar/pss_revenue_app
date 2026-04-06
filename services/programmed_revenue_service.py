import pandas as pd

from db_data_loader import load_programmed_revenue_source


def _safe_total_revenue(raw_df: pd.DataFrame) -> float:
    if raw_df is None or raw_df.empty or "Revenue" not in raw_df.columns:
        return 0.0
    return float(pd.to_numeric(raw_df["Revenue"], errors="coerce").fillna(0).sum())


def _safe_unique_tickets(raw_df: pd.DataFrame) -> int:
    if raw_df is None or raw_df.empty or "Nro_Ticket" not in raw_df.columns:
        return 0
    return int(raw_df["Nro_Ticket"].astype(str).nunique())


def prepare_programmed_revenue_outputs():
    raw_df = load_programmed_revenue_source()

    if raw_df is None:
        raw_df = pd.DataFrame()

    kpis = {
        "total_revenue": _safe_total_revenue(raw_df),
        "total_coupons": 0,
        "unique_tickets": _safe_unique_tickets(raw_df),
    }

    return {
        "raw_df": raw_df,
        "kpis": kpis,
    }