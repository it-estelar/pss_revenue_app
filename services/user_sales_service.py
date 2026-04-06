import pandas as pd
from sqlalchemy import create_engine, text

from config import get_database_url
from reports.user_sales_reports import (
    build_user_emisor,
    build_user_monthly,
    build_user_sales_base,
    build_user_summary,
    filter_user_sales_base,
)


def _get_engine():
    return create_engine(get_database_url(), future=True)


def get_user_catalog() -> pd.DataFrame:
    engine = _get_engine()

    query = """
        SELECT id, usuario, agente, estacion, activo
        FROM estelar_gds.admin_usuarios_emisores
        ORDER BY usuario
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df


def get_user_options() -> list[str]:
    catalog = get_user_catalog()
    if catalog.empty or "usuario" not in catalog.columns:
        return []

    if "activo" in catalog.columns:
        catalog = catalog[catalog["activo"].fillna(False) == True].copy()

    options = (
        catalog["usuario"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    options = sorted([x for x in options.unique().tolist() if x])
    return options


def prepare_sales_by_user_outputs(
    df: pd.DataFrame,
    selected_users: list[str] | None = None,
    top_n_emisores: int = 15,
):
    catalog_df = get_user_catalog()
    base_df = build_user_sales_base(df, catalog_df)

    matched_df = filter_user_sales_base(base_df, selected_users)

    summary_df = build_user_summary(matched_df)
    monthly_df = build_user_monthly(matched_df)
    emisor_df = build_user_emisor(matched_df, top_n=top_n_emisores)

    unmatched_df = base_df[base_df["usuario"].isna()].copy() if not base_df.empty else pd.DataFrame()

    kpis = {
        "total_revenue": float(matched_df["Revenue"].sum()) if not matched_df.empty else 0.0,
        "total_tickets": int(
            matched_df["Nro_Ticket"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        ) if not matched_df.empty else 0,
        "total_coupons": int(matched_df["Coupons Sold"].sum()) if not matched_df.empty else 0,
        "total_users": int(summary_df["USUARIO"].nunique()) if not summary_df.empty else 0,
    }

    coverage = {
        "unmatched_revenue": float(unmatched_df["Revenue"].sum()) if not unmatched_df.empty else 0.0,
        "unmatched_tickets": int(
            unmatched_df["Nro_Ticket"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        ) if not unmatched_df.empty else 0,
    }

    return {
        "user_options": get_user_options(),
        "summary_df": summary_df,
        "monthly_df": monthly_df,
        "emisor_df": emisor_df,
        "kpis": kpis,
        "coverage": coverage,
    }