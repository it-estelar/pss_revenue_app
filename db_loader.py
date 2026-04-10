from __future__ import annotations

"""
Low-level CSV-to-database loader for GDS ticket files.

Responsibilities
----------------
- Read the original CSV using the expected separator and encoding
- Normalize coupon-slot column names into a stable internal schema
- Convert source values into typed ticket-level fields
- Compute revenue, taxes, coupon count, and row hashes
- Detect current-vs-new ticket versions in the database
- Insert/update raw ticket records and coupon-detail records
- Maintain load-log entries for operational traceability

Important
---------
This is a low-level persistence module.
Do not put Streamlit rendering logic or BI/report aggregation here.
"""

import argparse
import hashlib
import json
import os
from utils import dedupe_columns, to_numeric_series, normalize_route, clean_text
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# -----------------------------------------------------------------------------
# CSV schema constants
# -----------------------------------------------------------------------------

CSV_SEP = ";"
CSV_ENCODING = "latin1"

CORE_COLS = [
    "Reporte",
    "FReporte",
    "Moneda",
    "Cambio",
    "Tipo Emisor",
    "Emisor",
    "Agente Reserva",
    "Agente Emisor",
    "Zona",
    "Pais",
    "Estado",
    "Localidad",
    "Nro_Ticket",
    "Date",
    "Transac",
    "Type",
    "Pax",
    "Pax_Type",
    "FOID",
    "Clave_Fiscal",
    "Cod_Reserva",
    "Fare_Calc",
    "Related_Doc",
]

FBASIS_COLS = [
    "FBasisCupon1",
    "FBasisCupon2",
    "FBasisCupon3",
    "FBasisCupon4",
]

COMMISSION_COLS = [
    "(C_CO) COMISION",
    "(E_EQ) Eqpd",
]

DROP_EXACT_COLS = {
    "(C_CV) IVA COMISION",
    "(O_CF) COSTO FINANCIERO",
    "(P_CA) EFECTIVO",
    "(P_CCVI) VISA",
    "(P_CCMC) MASTERCARD",
    "(P_CCDI) DINERS",
    "(P_CCAE) AMEX",
    "(P_CCO) OTROS",
    "MonedaQ1",
    "MonedaQ2",
    "MonedaQ3",
    "MonedaQ4",
    "ImporteQ1",
    "ImporteQ2",
    "ImporteQ3",
    "ImporteQ4",
    "STPO_1",
    "STPO_2",
    "STPO_3",
    "STPO_4",
    "Moneda Revenue_1",
    "Moneda Revenue_2",
    "Moneda Revenue_3",
    "Moneda Revenue_4",
    "Valor Revenue_1",
    "Valor Revenue_2",
    "Valor Revenue_3",
    "Valor Revenue_4",
}

COUPON_COLS = [
    "Nro Cupon_1",
    "Origen_1",
    "Destino_1",
    "Vuelo_1",
    "Clase_1",
    "Fecha Programada de vuelo_1",
    "Nro Cupon_2",
    "Origen_2",
    "Destino_2",
    "Vuelo_2",
    "Clase_2",
    "Fecha Programada de vuelo_2",
    "Nro Cupon_3",
    "Origen_3",
    "Destino_3",
    "Vuelo_3",
    "Clase_3",
    "Fecha Programada de vuelo_3",
    "Nro Cupon_4",
    "Origen_4",
    "Destino_4",
    "Vuelo_4",
    "Clase_4",
    "Fecha Programada de vuelo_4",
]

DATE_COLS = {
    "FReporte",
    "Date",
    "Fecha Programada de vuelo_1",
    "Fecha Programada de vuelo_2",
    "Fecha Programada de vuelo_3",
    "Fecha Programada de vuelo_4",
}

SCHEMA_NAME = "estelar_gds"
RAW_TABLE = f"{SCHEMA_NAME}.raw_gds_tickets"
LOAD_LOG_TABLE = f"{SCHEMA_NAME}.load_log"
COUPON_TABLE = f"{SCHEMA_NAME}.coupon_detail"

# -----------------------------------------------------------------------------
# Load stats model
# -----------------------------------------------------------------------------


@dataclass
class LoadStats:
    total_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0

# -----------------------------------------------------------------------------
# Source-column normalization helpers
# -----------------------------------------------------------------------------

def rename_coupon_blocks(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        # cupón 1
        "Nro Cupon": "Nro Cupon_1",
        "STPO": "STPO_1",
        "Origen": "Origen_1",
        "Destino": "Destino_1",
        "Carrier": "Carrier_1",
        "Vuelo": "Vuelo_1",
        "Clase": "Clase_1",
        "Fecha Programada de vuelo": "Fecha Programada de vuelo_1",
        "Moneda Revenue": "Moneda Revenue_1",
        "Valor Revenue": "Valor Revenue_1",

        # cupón 2 - formato con punto
        "Nro Cupon.1": "Nro Cupon_2",
        "STPO.1": "STPO_2",
        "Origen.1": "Origen_2",
        "Destino.1": "Destino_2",
        "Carrier.1": "Carrier_2",
        "Vuelo.1": "Vuelo_2",
        "Clase.1": "Clase_2",
        "Fecha Programada de vuelo.1": "Fecha Programada de vuelo_2",
        "Moneda Revenue.1": "Moneda Revenue_2",
        "Valor Revenue.1": "Valor Revenue_2",

        # cupón 3 - formato con punto
        "Nro Cupon.2": "Nro Cupon_3",
        "STPO.2": "STPO_3",
        "Origen.2": "Origen_3",
        "Destino.2": "Destino_3",
        "Carrier.2": "Carrier_3",
        "Vuelo.2": "Vuelo_3",
        "Clase.2": "Clase_3",
        "Fecha Programada de vuelo.2": "Fecha Programada de vuelo_3",
        "Moneda Revenue.2": "Moneda Revenue_3",
        "Valor Revenue.2": "Valor Revenue_3",

        # cupón 4 - formato con punto
        "Nro Cupon.3": "Nro Cupon_4",
        "STPO.3": "STPO_4",
        "Origen.3": "Origen_4",
        "Destino.3": "Destino_4",
        "Carrier.3": "Carrier_4",
        "Vuelo.3": "Vuelo_4",
        "Clase.3": "Clase_4",
        "Fecha Programada de vuelo.3": "Fecha Programada de vuelo_4",
        "Moneda Revenue.3": "Moneda Revenue_4",
        "Valor Revenue.3": "Valor Revenue_4",

        # soporte por si el archivo ya viniera con sufijos _2/_3/_4
        "Nro Cupon_2": "Nro Cupon_2",
        "STPO_2": "STPO_2",
        "Origen_2": "Origen_2",
        "Destino_2": "Destino_2",
        "Carrier_2": "Carrier_2",
        "Vuelo_2": "Vuelo_2",
        "Clase_2": "Clase_2",
        "Fecha Programada de vuelo_2": "Fecha Programada de vuelo_2",
        "Moneda Revenue_2": "Moneda Revenue_2",
        "Valor Revenue_2": "Valor Revenue_2",

        "Nro Cupon_3": "Nro Cupon_3",
        "STPO_3": "STPO_3",
        "Origen_3": "Origen_3",
        "Destino_3": "Destino_3",
        "Carrier_3": "Carrier_3",
        "Vuelo_3": "Vuelo_3",
        "Clase_3": "Clase_3",
        "Fecha Programada de vuelo_3": "Fecha Programada de vuelo_3",
        "Moneda Revenue_3": "Moneda Revenue_3",
        "Valor Revenue_3": "Valor Revenue_3",

        "Nro Cupon_4": "Nro Cupon_4",
        "STPO_4": "STPO_4",
        "Origen_4": "Origen_4",
        "Destino_4": "Destino_4",
        "Carrier_4": "Carrier_4",
        "Vuelo_4": "Vuelo_4",
        "Clase_4": "Clase_4",
        "Fecha Programada de vuelo_4": "Fecha Programada de vuelo_4",
        "Moneda Revenue_4": "Moneda Revenue_4",
        "Valor Revenue_4": "Valor Revenue_4",
    }
    return df.rename(columns=rename_map)




def to_date_value(value: Any) -> Any:
    txt = str(value).strip()
    if txt in {"", "nan", "None", "NULL"}:
        return None
    dt = pd.to_datetime(txt, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()


def normalize_hash_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, float):
        return round(value, 6)
    txt = str(value).strip()
    return txt if txt != "" else None


def stable_row_hash(row: pd.Series, cols: list[str]) -> str:
    payload = {col: normalize_hash_value(row.get(col)) for col in cols}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def chunked(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def dedupe_latest_rows_by_ticket(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the last occurrence of each ticket_key inside the same source file."""
    if df.empty or "ticket_key" not in df.columns:
        return df

    out = df.copy()
    out["_source_order"] = range(len(out))
    out = out.sort_values("_source_order").drop_duplicates(subset=["ticket_key"], keep="last")
    out = out.sort_values("_source_order").drop(columns=["_source_order"]).reset_index(drop=True)
    return out

# -----------------------------------------------------------------------------
# Database and schema helpers
# -----------------------------------------------------------------------------

def get_engine(db_url: str) -> Engine:
    return create_engine(db_url, future=True)


def configure_statement_timeout(conn) -> None:
    """
    Set a transaction-local statement timeout for the loader session.

    Environment variable:
    - DB_LOADER_STATEMENT_TIMEOUT_MS
      - "0" (default): no timeout for statements in this transaction
      - positive integer: timeout in milliseconds
    """
    timeout_raw = str(os.getenv("DB_LOADER_STATEMENT_TIMEOUT_MS", "0")).strip()
    try:
        timeout_ms = int(timeout_raw)
    except ValueError:
        timeout_ms = 0

    if timeout_ms < 0:
        timeout_ms = 0

    conn.execute(text("SET LOCAL statement_timeout = :timeout_ms"), {"timeout_ms": timeout_ms})

def get_table_columns(conn, table_name: str) -> set[str]:
    schema, table = table_name.split(".", 1)
    sql = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
        """
    )
    rows = conn.execute(sql, {"schema": schema, "table": table}).fetchall()
    return {r[0] for r in rows}


def quote_identifier(col_name: str) -> str:
    return '"' + str(col_name).replace('"', '""') + '"'

# -----------------------------------------------------------------------------
# Source CSV reading and raw-frame preparation
# -----------------------------------------------------------------------------

def read_source_csv(csv_path: str | Path) -> pd.DataFrame:
    """
    Read the original GDS CSV and normalize duplicate/slot-based column names.
    """
    df = pd.read_csv(
        csv_path,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        engine="python",
    )
    df.columns = dedupe_columns(df.columns.tolist())

    unnamed_like = [
        c for c in df.columns
        if str(c).strip() == "" or str(c).startswith("Unnamed")
    ]
    if unnamed_like:
        df = df.drop(columns=unnamed_like, errors="ignore")

    df = rename_coupon_blocks(df)
    return df


def pick_tax_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).startswith("(T_")]


def pick_ref_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).strip().startswith("Ref")]


def ensure_required_columns(df: pd.DataFrame) -> None:
    required = {"Nro_Ticket", "Cambio", "(C_CO) COMISION", "(E_EQ) Eqpd"}
    missing = sorted([c for c in required if c not in df.columns])
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {missing}")


def build_selected_raw_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:

    """
    Build the cleaned raw ticket-level dataframe used for DB persistence.

    This step:
    - validates required columns
    - keeps only the supported source columns
    - converts dates and numeric fields
    - computes taxes, revenue, coupon count, ticket_key, and row_hash
    """
    
    ensure_required_columns(df)

    tax_cols = pick_tax_columns(df)
    ref_cols = pick_ref_columns(df)

    keep_cols = set(CORE_COLS + FBASIS_COLS + COMMISSION_COLS + COUPON_COLS + tax_cols)
    keep_cols = [c for c in df.columns if c in keep_cols and c not in DROP_EXACT_COLS and c not in ref_cols]

    out = df[keep_cols].copy()

    for col in DATE_COLS:
        if col in out.columns:
            out[col] = out[col].apply(to_date_value)

    out["Cambio_num"] = to_numeric_series(out["Cambio"]) if "Cambio" in out.columns else 0.0

    if "(C_CO) COMISION" in out.columns:
        out["(C_CO) COMISION"] = to_numeric_series(out["(C_CO) COMISION"])
        out["comision_num"] = out["(C_CO) COMISION"]
    else:
        out["comision_num"] = 0.0

    if "(E_EQ) Eqpd" in out.columns:
        out["(E_EQ) Eqpd"] = to_numeric_series(out["(E_EQ) Eqpd"])
        out["eqpd_num"] = out["(E_EQ) Eqpd"]
    else:
        out["eqpd_num"] = 0.0

    for col in tax_cols:
        if col in out.columns:
            out[col] = to_numeric_series(out[col])

    out["tax_total"] = out[tax_cols].sum(axis=1) if tax_cols else 0.0
    out["revenue_total"] = (out["comision_num"] + out["eqpd_num"] + out["tax_total"]) * out["Cambio_num"]

    coupon_num_cols = [c for c in [f"Nro Cupon_{i}" for i in range(1, 5)] if c in out.columns]
    if coupon_num_cols:
        coupon_presence = pd.DataFrame({
            col: out[col].astype(str).str.strip().replace({"nan": "", "None": ""}).ne("")
            for col in coupon_num_cols
        })
        out["coupons_sold"] = coupon_presence.sum(axis=1)
    else:
        out["coupons_sold"] = 0

    out["ticket_key"] = out["Nro_Ticket"].astype(str).str.strip()
    out = out[out["ticket_key"] != ""].copy()

    hash_cols = [c for c in out.columns if c not in {"Cambio_num", "comision_num", "eqpd_num"}]
    out["row_hash"] = out.apply(lambda r: stable_row_hash(r, hash_cols), axis=1)

    return out, tax_cols

# -----------------------------------------------------------------------------
# Load-log helpers
# -----------------------------------------------------------------------------

def create_load_log(conn, file_name: str, file_size_bytes: int | None, load_type: str) -> int:
    sql = text(
        f"""
        INSERT INTO {LOAD_LOG_TABLE} (
            file_name,
            file_size_bytes,
            load_type,
            started_at,
            status
        )
        VALUES (
            :file_name,
            :file_size_bytes,
            :load_type,
            now(),
            'running'
        )
        RETURNING load_id
        """
    )
    return conn.execute(
        sql,
        {
            "file_name": file_name,
            "file_size_bytes": file_size_bytes,
            "load_type": load_type,
        },
    ).scalar_one()


def close_load_log(conn, load_id: int, stats: LoadStats, status: str, error_message: str | None = None) -> None:
    sql = text(
        f"""
        UPDATE {LOAD_LOG_TABLE}
        SET ended_at = now(),
            status = :status,
            total_rows = :total_rows,
            inserted_rows = :inserted_rows,
            updated_rows = :updated_rows,
            skipped_rows = :skipped_rows,
            error_rows = :error_rows,
            error_message = :error_message
        WHERE load_id = :load_id
        """
    )
    conn.execute(
        sql,
        {
            "load_id": load_id,
            "status": status,
            "total_rows": stats.total_rows,
            "inserted_rows": stats.inserted_rows,
            "updated_rows": stats.updated_rows,
            "skipped_rows": stats.skipped_rows,
            "error_rows": stats.error_rows,
            "error_message": error_message,
        },
    )

# -----------------------------------------------------------------------------
# Current-version lookup helpers
# -----------------------------------------------------------------------------

def fetch_existing_current_by_tickets(conn, ticket_keys: list[str]) -> dict[str, dict[str, Any]]:
    if not ticket_keys:
        return {}

    out: dict[str, dict[str, Any]] = {}
    sql = text(
        f"""
        SELECT raw_ticket_id, ticket_key, row_hash, version_num
        FROM {RAW_TABLE}
        WHERE is_current = true
          AND ticket_key = ANY(:ticket_keys)
        """
    )

    rows = conn.execute(sql, {"ticket_keys": ticket_keys}).mappings().all()
    for row in rows:
        out[str(row["ticket_key"])] = dict(row)
    return out


def fetch_raw_table_columns(conn) -> set[str]:
    return get_table_columns(conn, RAW_TABLE)


# -----------------------------------------------------------------------------
# Raw-table and coupon-detail persistence helpers
# -----------------------------------------------------------------------------

def insert_raw_row(conn, raw_row: dict[str, Any]) -> int:
    cols = list(raw_row.keys())
    quoted_cols = ", ".join([quote_identifier(c) for c in cols])

    bind_map: dict[str, Any] = {}
    placeholders: list[str] = []

    for i, col in enumerate(cols):
        param_name = f"p{i}"
        placeholders.append(f":{param_name}")
        bind_map[param_name] = raw_row[col]

    values_sql = ", ".join(placeholders)

    sql = text(
        f"""
        INSERT INTO {RAW_TABLE} ({quoted_cols})
        VALUES ({values_sql})
        RETURNING raw_ticket_id
        """
    )
    return conn.execute(sql, bind_map).scalar_one()


def close_current_version(conn, raw_ticket_id: int) -> None:
    conn.execute(
        text(
            f"""
            UPDATE {RAW_TABLE}
            SET is_current = false
            WHERE raw_ticket_id = :raw_ticket_id
            """
        ),
        {"raw_ticket_id": raw_ticket_id},
    )


def delete_coupon_detail_for_raw(conn, raw_ticket_id: int) -> None:
    conn.execute(
        text(f"DELETE FROM {COUPON_TABLE} WHERE raw_ticket_id = :raw_ticket_id"),
        {"raw_ticket_id": raw_ticket_id},
    )


def insert_coupon_rows(conn, coupon_rows: list[dict[str, Any]]) -> None:
    if not coupon_rows:
        return

    cols = list(coupon_rows[0].keys())
    quoted_cols = ", ".join([quote_identifier(c) for c in cols])

    sql_rows: list[str] = []
    params: dict[str, Any] = {}

    for row_idx, row in enumerate(coupon_rows):
        row_placeholders: list[str] = []
        for col_idx, col in enumerate(cols):
            param_name = f"r{row_idx}_c{col_idx}"
            row_placeholders.append(f":{param_name}")
            params[param_name] = row[col]
        sql_rows.append(f"({', '.join(row_placeholders)})")

    sql = text(
        f"""
        INSERT INTO {COUPON_TABLE} ({quoted_cols})
        VALUES {', '.join(sql_rows)}
        """
    )

    conn.execute(sql, params)


def build_raw_insert_payload(
    row: pd.Series,
    raw_table_columns: set[str],
    load_id: int,
    source_file: str,
    version_num: int,
    previous_raw_ticket_id: int | None,
) -> dict[str, Any]:
     
    """
    Build the insert payload for a single raw ticket row.
    """
    payload: dict[str, Any] = {
        "load_id": load_id,
        "source_file": source_file,
        "ticket_key": clean_text(row.get("ticket_key")),
        "row_hash": clean_text(row.get("row_hash")),
        "is_current": True,
        "version_num": version_num,
        "previous_raw_ticket_id": previous_raw_ticket_id,
        "tax_total": float(row.get("tax_total", 0) or 0),
        "revenue_total": float(row.get("revenue_total", 0) or 0),
        "coupons_sold": int(row.get("coupons_sold", 0) or 0),
    }

    for col in row.index:
        if col in {
            "Cambio_num",
            "comision_num",
            "eqpd_num",
            "ticket_key",
            "row_hash",
            "tax_total",
            "revenue_total",
            "coupons_sold",
        }:
            continue

        if col not in raw_table_columns:
            continue

        val = row[col]

        if col in DATE_COLS:
            payload[col] = to_date_value(val)
        elif col in {"(C_CO) COMISION", "(E_EQ) Eqpd"} or str(col).startswith("(T_"):
            payload[col] = float(val) if pd.notna(val) else None
        else:
            payload[col] = clean_text(val)

    payload = {k: v for k, v in payload.items() if k in raw_table_columns}
    return payload


def build_coupon_rows(row: pd.Series, raw_ticket_id: int, load_id: int) -> list[dict[str, Any]]:
    """
    Build coupon-detail rows for the normalized coupon slots present in one ticket row.
    """
    rows: list[dict[str, Any]] = []

    for seq in range(1, 5):
        coupon_number = clean_text(row.get(f"Nro Cupon_{seq}"))
        origen = clean_text(row.get(f"Origen_{seq}"))
        destino = clean_text(row.get(f"Destino_{seq}"))
        clase = clean_text(row.get(f"Clase_{seq}"))
        vuelo = clean_text(row.get(f"Vuelo_{seq}"))
        fecha_programada = to_date_value(row.get(f"Fecha Programada de vuelo_{seq}"))
        fbasis = clean_text(row.get(f"FBasisCupon{seq}"))

        if not coupon_number or not origen or not destino:
            continue

        ruta = normalize_route(origen, destino)
        if not ruta:
            continue

        rows.append(
            {
                "raw_ticket_id": raw_ticket_id,
                "load_id": load_id,
                "ticket_key": clean_text(row.get("ticket_key")),
                "row_hash": clean_text(row.get("row_hash")),
                "is_current": True,
                "coupon_seq": seq,
                "coupon_number": coupon_number,
                "report_date": to_date_value(row.get("FReporte")),
                "issue_date": to_date_value(row.get("Date")),
                "currency_code": clean_text(row.get("Moneda")),
                "exchange_rate": float(row.get("Cambio_num", 0) or 0),
                "emisor": clean_text(row.get("Emisor")),
                "tipo_emisor": clean_text(row.get("Tipo Emisor")),
                "agente_reserva": clean_text(row.get("Agente Reserva")),
                "agente_emisor": clean_text(row.get("Agente Emisor")),
                "pax": clean_text(row.get("Pax")),
                "pax_type": clean_text(row.get("Pax_Type")),
                "foid": clean_text(row.get("FOID")),
                "clave_fiscal": clean_text(row.get("Clave_Fiscal")),
                "cod_reserva": clean_text(row.get("Cod_Reserva")),
                "transac": clean_text(row.get("Transac")),
                "type_doc": clean_text(row.get("Type")),
                "origen": origen.upper(),
                "destino": destino.upper(),
                "vuelo": vuelo,
                "clase": clase.upper() if clase else None,
                "fecha_programada": fecha_programada,
                "fbasis": fbasis,
                "ruta_normalizada": ruta,
                "revenue_total": float(row.get("revenue_total", 0) or 0),
                "tax_total": float(row.get("tax_total", 0) or 0),
            }
        )

    return rows

# -----------------------------------------------------------------------------
# Main CSV load execution
# -----------------------------------------------------------------------------

def process_csv_to_database(csv_path: str | Path, db_url: str, load_type: str = "incremental") -> LoadStats:

    """
    Execute the end-to-end CSV load into raw ticket and coupon-detail tables.

    Flow
    ----
    1. Read and normalize the source CSV
    2. Build the ticket-level persistence dataframe
    3. Compare incoming tickets against current DB versions
    4. Insert new rows or version existing rows
    5. Rebuild coupon-detail rows for the inserted raw version
    6. Update the operational load log
    """

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {csv_path}")

    stats = LoadStats()
    df_source = read_source_csv(csv_path)
    df, _tax_cols = build_selected_raw_frame(df_source)
    stats.total_rows = int(len(df))
    df = dedupe_latest_rows_by_ticket(df)

    engine = get_engine(db_url)

    with engine.begin() as conn:
        load_id = create_load_log(
            conn=conn,
            file_name=csv_path.name,
            file_size_bytes=csv_path.stat().st_size if csv_path.exists() else None,
            load_type=load_type,
        )

    try:
        with engine.begin() as conn:
            raw_table_columns = fetch_raw_table_columns(conn)
            configure_statement_timeout(conn)

            ticket_keys = df["ticket_key"].astype(str).tolist()
            existing_map: dict[str, dict[str, Any]] = {}
            for chunk in chunked(ticket_keys, 5000):
                existing_map.update(fetch_existing_current_by_tickets(conn, chunk))

            for _, row in df.iterrows():
                ticket_key = str(row["ticket_key"]).strip()
                row_hash = str(row["row_hash"]).strip()

                existing = existing_map.get(ticket_key)

                if existing and str(existing["row_hash"]) == row_hash:
                    stats.skipped_rows += 1
                    continue

                previous_raw_ticket_id = None
                version_num = 1

                try:
                    with conn.begin_nested():
                        if existing:
                            previous_raw_ticket_id = int(existing["raw_ticket_id"])
                            version_num = int(existing["version_num"]) + 1
                            close_current_version(conn, previous_raw_ticket_id)
                            delete_coupon_detail_for_raw(conn, previous_raw_ticket_id)
                            stats.updated_rows += 1
                        else:
                            stats.inserted_rows += 1

                        raw_payload = build_raw_insert_payload(
                            row=row,
                            raw_table_columns=raw_table_columns,
                            load_id=load_id,
                            source_file=csv_path.name,
                            version_num=version_num,
                            previous_raw_ticket_id=previous_raw_ticket_id,
                        )

                        raw_ticket_id = insert_raw_row(conn, raw_payload)

                        coupon_rows = build_coupon_rows(
                            row=row,
                            raw_ticket_id=raw_ticket_id,
                            load_id=load_id,
                        )
                        insert_coupon_rows(conn, coupon_rows)

                    existing_map[ticket_key] = {
                        "raw_ticket_id": raw_ticket_id,
                        "ticket_key": ticket_key,
                        "row_hash": row_hash,
                        "version_num": version_num,
                    }
                except Exception:
                    if existing:
                        stats.updated_rows -= 1
                    else:
                        stats.inserted_rows -= 1
                    stats.error_rows += 1
                    raise

                existing_map[ticket_key] = {
                    "raw_ticket_id": raw_ticket_id,
                    "ticket_key": ticket_key,
                    "row_hash": row_hash,
                    "version_num": version_num,
                }

        with engine.begin() as conn:
            close_load_log(conn, load_id, stats, status="completed")

        return stats

    except Exception as exc:
        stats.error_rows += 1

        try:
            with engine.begin() as conn:
                close_load_log(
                    conn,
                    load_id,
                    stats,
                    status="failed",
                    error_message=str(exc),
                )
        except Exception:
            pass

        raise

# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Carga masiva o incremental de CSV GDS a PostgreSQL.")
    parser.add_argument("csv_path", help="Ruta del archivo CSV")
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", ""),
        help="Cadena de conexión PostgreSQL. También puede venir de DATABASE_URL",
    )
    parser.add_argument(
        "--load-type",
        choices=["massive", "incremental"],
        default="incremental",
        help="Tipo de carga",
    )

    args = parser.parse_args()

    if not args.db_url:
        raise ValueError("Debes pasar --db-url o definir la variable de entorno DATABASE_URL")

    started = datetime.now(timezone.utc)
    stats = process_csv_to_database(
        csv_path=args.csv_path,
        db_url=args.db_url,
        load_type=args.load_type,
    )
    ended = datetime.now(timezone.utc)

    print("Carga completada.")
    print(f"Inicio UTC:   {started.isoformat()}")
    print(f"Fin UTC:      {ended.isoformat()}")
    print(f"Total rows:   {stats.total_rows}")
    print(f"Inserted:     {stats.inserted_rows}")
    print(f"Updated:      {stats.updated_rows}")
    print(f"Skipped:      {stats.skipped_rows}")
    print(f"Errors:       {stats.error_rows}")


if __name__ == "__main__":
    main()