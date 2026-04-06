from __future__ import annotations

"""
Database-backed analytic loaders for the Streamlit application.

Responsibilities
----------------
- Read the standard ticket-level analytic frame from the current raw DB view
- Read the coupon-level analytic frame from the current coupon DB view
- Normalize and clean columns used across modules
- Build shell KPI values for standard analytic modules
- Expose a separate source loader for Programmed Revenue / Volado

Important
---------
This file is part of the data-access layer.
Do not put Streamlit page rendering or business-report aggregation here.
"""

from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from config import get_database_url


# -----------------------------------------------------------------------------
# Database views
# -----------------------------------------------------------------------------

SCHEMA_NAME = "estelar_gds"
RAW_CURRENT_VIEW = f"{SCHEMA_NAME}.v_raw_gds_tickets_current"
COUPON_CURRENT_VIEW = f"{SCHEMA_NAME}.v_coupon_detail_current"


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------

def _get_engine():
    """
    Create a SQLAlchemy engine using the configured DATABASE_URL.
    """
    return create_engine(get_database_url(), future=True)


def _build_date_filter_sql(
    column_name: str,
    date_from: Any,
    date_to: Any,
    params: dict[str, Any],
    prefix: str,
) -> str:
    """
    Build a parameterized SQL date filter fragment for a single column.
    """
    clauses = []

    if date_from:
        params[f"{prefix}_from"] = date_from
        clauses.append(f"{column_name} >= :{prefix}_from")

    if date_to:
        params[f"{prefix}_to"] = date_to
        clauses.append(f"{column_name} <= :{prefix}_to")

    return " AND ".join(clauses)


def _to_numeric(values, default: float = 0.0):
    """
    Convert a scalar or Series to numeric, applying a fallback default.
    """
    converted = pd.to_numeric(values, errors="coerce")

    if isinstance(converted, pd.Series):
        return converted.fillna(default)

    if pd.isna(converted):
        return default

    return converted


# -----------------------------------------------------------------------------
# Standard analytic module loader
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_db_data(date_from=None, date_to=None):
    """
    Load the standard analytic payload used by most modules.

    Returns
    -------
    tuple:
        df           -> ticket/raw-level analytic dataframe
        coupons_long -> coupon-level analytic dataframe
        kpis         -> shell KPI dictionary
        tax_columns  -> currently reserved for compatibility
        routes       -> normalized route options derived from coupon data
    """
    engine = _get_engine()
    params: dict[str, Any] = {}

    raw_where = []
    coupon_where = []

    raw_date_filter = _build_date_filter_sql('"Date"', date_from, date_to, params, "raw_date")
    coupon_date_filter = _build_date_filter_sql("issue_date", date_from, date_to, params, "coupon_date")

    if raw_date_filter:
        raw_where.append(raw_date_filter)
    if coupon_date_filter:
        coupon_where.append(coupon_date_filter)

    raw_where_sql = f"WHERE {' AND '.join(raw_where)}" if raw_where else ""
    coupon_where_sql = f"WHERE {' AND '.join(coupon_where)}" if coupon_where else ""

    raw_sql = f"""
        SELECT
            "Emisor",
            "Moneda",
            revenue_total AS "Revenue",
            coupons_sold AS "Coupons Sold",
            "Nro_Ticket",
            "Date",
            "Tipo Emisor",
            "Agente Reserva",
            "Agente Emisor",
            "Pax",
            "Pax_Type",
            "FOID",
            "Clave_Fiscal",
            "Cod_Reserva",
            "Transac",
            "Type",
            "Clase_1",
            "Clase_2",
            "Clase_3",
            "Clase_4",
            "Nro Cupon_1",
            "Nro Cupon_2",
            "Nro Cupon_3",
            "Nro Cupon_4"
        FROM {RAW_CURRENT_VIEW}
        {raw_where_sql}
    """

    coupon_sql = f"""
        SELECT
            emisor AS "Emisor",
            currency_code AS "Moneda",
            ticket_key AS "Ticket_Key",
            raw_ticket_id AS "Raw_Ticket_ID",
            revenue_total AS "Revenue Total",
            COUNT(*) OVER (
                PARTITION BY ticket_key
            ) AS "Coupon Count Ticket",
            CASE
                WHEN COUNT(*) OVER (PARTITION BY ticket_key) > 0
                    THEN revenue_total / COUNT(*) OVER (PARTITION BY ticket_key)
                ELSE revenue_total
            END AS "Revenue",
            clase AS "Clase",
            coupon_number AS "Nro Cupon",
            origen AS "Origen",
            destino AS "Destino",
            ruta_normalizada AS "Ruta",
            issue_date AS "Date",
            tipo_emisor AS "Tipo Emisor",
            agente_reserva AS "Agente Reserva",
            agente_emisor AS "Agente Emisor",
            pax AS "Pax",
            pax_type AS "Pax_Type",
            foid AS "FOID",
            clave_fiscal AS "Clave_Fiscal",
            cod_reserva AS "Cod_Reserva",
            transac AS "Transac",
            type_doc AS "Type",
            vuelo AS "Vuelo",
            fecha_programada AS "Fecha Programada de vuelo",
            fbasis AS "FBasis"
        FROM {COUPON_CURRENT_VIEW}
        {coupon_where_sql}
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(raw_sql), conn, params=params)
        coupons_long = pd.read_sql(text(coupon_sql), conn, params=params)

    if df.empty:
        kpis = {
            "rows": 0,
            "total_revenue": 0.0,
            "total_coupons": 0,
            "unique_tickets": 0,
        }
        return df, coupons_long, kpis, [], []

    # -------------------------------------------------------------------------
    # Raw / ticket-level cleanup
    # -------------------------------------------------------------------------

    df["Emisor"] = df["Emisor"].fillna("").astype(str).str.strip()
    df.loc[df["Emisor"] == "", "Emisor"] = "SIN EMISOR"

    df["Revenue"] = _to_numeric(df["Revenue"], default=0.0)
    df["Coupons Sold"] = _to_numeric(df["Coupons Sold"], default=0).astype(int)

    for col in [
        "Moneda",
        "Nro_Ticket",
        "Tipo Emisor",
        "Agente Reserva",
        "Agente Emisor",
        "Pax",
        "Pax_Type",
        "FOID",
        "Clave_Fiscal",
        "Cod_Reserva",
        "Transac",
        "Type",
        "Clase_1",
        "Clase_2",
        "Clase_3",
        "Clase_4",
        "Nro Cupon_1",
        "Nro Cupon_2",
        "Nro Cupon_3",
        "Nro Cupon_4",
    ]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    for col in ["Clase_1", "Clase_2", "Clase_3", "Clase_4"]:
        if col in df.columns:
            df[col] = df[col].str.upper()

    df["Moneda"] = df["Moneda"].str.upper()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # -------------------------------------------------------------------------
    # Coupon-level cleanup
    # -------------------------------------------------------------------------

    if not coupons_long.empty:
        coupons_long["Emisor"] = coupons_long["Emisor"].fillna("").astype(str).str.strip()
        coupons_long.loc[coupons_long["Emisor"] == "", "Emisor"] = "SIN EMISOR"

        coupons_long["Ticket_Key"] = coupons_long["Ticket_Key"].fillna("").astype(str).str.strip()
        coupons_long["Revenue Total"] = _to_numeric(coupons_long["Revenue Total"], default=0.0)
        coupons_long["Coupon Count Ticket"] = _to_numeric(
            coupons_long["Coupon Count Ticket"], default=0
        ).astype(int)
        coupons_long["Revenue"] = _to_numeric(coupons_long["Revenue"], default=0.0)

        coupons_long["Clase"] = coupons_long["Clase"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Nro Cupon"] = coupons_long["Nro Cupon"].fillna("").astype(str).str.strip()
        coupons_long["Origen"] = coupons_long["Origen"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Destino"] = coupons_long["Destino"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Ruta"] = coupons_long["Ruta"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Moneda"] = coupons_long["Moneda"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["FOID"] = coupons_long["FOID"].fillna("").astype(str).str.strip()
        coupons_long["Clave_Fiscal"] = coupons_long["Clave_Fiscal"].fillna("").astype(str).str.strip()
        coupons_long["Cod_Reserva"] = coupons_long["Cod_Reserva"].fillna("").astype(str).str.strip()
        coupons_long["Pax"] = coupons_long["Pax"].fillna("").astype(str).str.strip()
        coupons_long["Transac"] = coupons_long["Transac"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Type"] = coupons_long["Type"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["Vuelo"] = coupons_long["Vuelo"].fillna("").astype(str).str.strip().str.upper()
        coupons_long["FBasis"] = coupons_long["FBasis"].fillna("").astype(str).str.strip().str.upper()

        coupons_long["Date"] = pd.to_datetime(coupons_long["Date"], errors="coerce")
        coupons_long["Fecha Programada de vuelo"] = pd.to_datetime(
            coupons_long["Fecha Programada de vuelo"],
            errors="coerce",
        )

        coupons_long = coupons_long[
            (coupons_long["Clase"] != "")
            & (coupons_long["Nro Cupon"] != "")
            & (coupons_long["Ruta"] != "")
        ].copy()

    # -------------------------------------------------------------------------
    # Shell KPI payload
    # -------------------------------------------------------------------------

    kpis = {
        "rows": int(len(df)),
        "total_revenue": float(df["Revenue"].sum()),
        "total_coupons": int(df["Coupons Sold"].sum()),
        "unique_tickets": int(
            df["Nro_Ticket"]
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        ) if "Nro_Ticket" in df.columns else 0,
    }

    routes = sorted(set(coupons_long["Ruta"].astype(str).tolist())) if not coupons_long.empty else []
    tax_columns = []

    return df, coupons_long, kpis, tax_columns, routes


# -----------------------------------------------------------------------------
# Infrastructure checks
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def test_db_connection():
    """
    Lightweight DB health check used by app startup.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


# -----------------------------------------------------------------------------
# Specialized source for Programmed Revenue / Volado
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_programmed_revenue_source():
    """
    Load the raw source frame used by Programmed Revenue and Volado.

    This path intentionally stays separate from load_db_data() because those
    modules rely on coupon-slot reconstruction from the raw ticket view.
    """
    engine = _get_engine()

    sql = f"""
        SELECT
            "Nro_Ticket",
            "Transac",
            "Related_Doc",
            "Emisor",
            "Pax",
            "Cod_Reserva",
            "FOID",
            revenue_total AS "Revenue",

            "FBasisCupon1",
            "FBasisCupon2",
            "FBasisCupon3",
            "FBasisCupon4",

            "Origen_1" AS "Origen",
            "Destino_1" AS "Destino",
            "Vuelo_1" AS "Vuelo",
            "Clase_1" AS "Clase",
            "Fecha Programada de vuelo_1" AS "Fecha Programada de vuelo",

            "Origen_2" AS "Origen.1",
            "Destino_2" AS "Destino.1",
            "Vuelo_2" AS "Vuelo.1",
            "Clase_2" AS "Clase.1",
            "Fecha Programada de vuelo_2" AS "Fecha Programada de vuelo.1",

            "Origen_3" AS "Origen.2",
            "Destino_3" AS "Destino.2",
            "Vuelo_3" AS "Vuelo.2",
            "Clase_3" AS "Clase.2",
            "Fecha Programada de vuelo_3" AS "Fecha Programada de vuelo.2",

            "Origen_4" AS "Origen.3",
            "Destino_4" AS "Destino.3",
            "Vuelo_4" AS "Vuelo.3",
            "Clase_4" AS "Clase.3",
            "Fecha Programada de vuelo_4" AS "Fecha Programada de vuelo.3"
        FROM {RAW_CURRENT_VIEW}
        WHERE "Transac" IN ('TKTT', 'EMDA')
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)

    if df.empty:
        return df

    df["Nro_Ticket"] = df["Nro_Ticket"].astype(str).str.strip()
    df["Transac"] = df["Transac"].astype(str).str.strip().str.upper()
    df["Emisor"] = df["Emisor"].astype(str).str.strip()
    df["Pax"] = df["Pax"].astype(str).str.strip()
    df["Cod_Reserva"] = df["Cod_Reserva"].astype(str).str.strip()
    df["FOID"] = df["FOID"].astype(str).str.strip()

    if "Related_Doc" in df.columns:
        df["Related_Doc"] = df["Related_Doc"].astype(str).str.strip()
    else:
        df["Related_Doc"] = ""

    df["Revenue"] = _to_numeric(df["Revenue"], default=0.0)

    return df