from __future__ import annotations

"""
Service-layer helpers for the Data Load module.

Responsibilities
----------------
- Save uploaded Streamlit files into temporary local files
- Build preview/validation stats before running a load
- Execute the selected load mode against the database
- Fetch recent load-log history for the UI

Important
---------
This file orchestrates the data-load workflow.
It should not contain Streamlit rendering logic.
"""

import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config import get_database_url
from db_loader import (
    build_selected_raw_frame,
    fetch_existing_current_by_tickets,
    process_csv_to_database,
    read_source_csv,
)

SCHEMA_NAME = "estelar_gds"
LOAD_LOG_TABLE = f"{SCHEMA_NAME}.load_log"


def get_engine() -> Engine:
    """
    Build the SQLAlchemy engine for data-load operations.
    """
    db_url = get_database_url().strip()
    if not db_url:
        raise ValueError("No hay DATABASE URL configurado.")
    return create_engine(db_url, future=True)


def save_uploaded_file_to_temp(uploaded_file: UploadedFile) -> str:
    """
    Persist an uploaded Streamlit file to a temporary local path.
    """
    suffix = Path(uploaded_file.name).suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def preview_uploaded_csv(uploaded_file: UploadedFile) -> dict[str, Any]:
    """
    Build a preview payload for the uploaded CSV.

    This includes:
    - rows and unique tickets in file
    - duplicate tickets inside the file
    - file date range
    - estimated insert/update/skip counts against current DB state
    - required-column validation
    """
    temp_path = save_uploaded_file_to_temp(uploaded_file)

    try:
        df_source = read_source_csv(temp_path)
        df, _tax_cols = build_selected_raw_frame(df_source)

        total_rows = int(len(df))
        unique_tickets_in_file = int(df["ticket_key"].nunique()) if not df.empty else 0
        duplicate_tickets_in_file = int(total_rows - unique_tickets_in_file)

        date_min = None
        date_max = None
        if not df.empty and "Date" in df.columns:
            date_series = pd.to_datetime(df["Date"], errors="coerce").dropna()
            if not date_series.empty:
                date_min = date_series.min().date()
                date_max = date_series.max().date()

        ticket_keys = df["ticket_key"].astype(str).tolist() if not df.empty else []

        existing_map: dict[str, dict[str, Any]] = {}
        if ticket_keys:
            engine = get_engine()
            with engine.connect() as conn:
                chunk_size = 5000
                for i in range(0, len(ticket_keys), chunk_size):
                    chunk = ticket_keys[i:i + chunk_size]
                    existing_map.update(fetch_existing_current_by_tickets(conn, chunk))

        would_insert = 0
        would_update = 0
        would_skip = 0

        for _, row in df.iterrows():
            ticket_key = str(row["ticket_key"]).strip()
            row_hash = str(row["row_hash"]).strip()
            existing = existing_map.get(ticket_key)

            if not existing:
                would_insert += 1
            elif str(existing["row_hash"]) == row_hash:
                would_skip += 1
            else:
                would_update += 1

        missing_required: list[str] = []
        required = {"Nro_Ticket", "Cambio", "(C_CO) COMISION", "(E_EQ) Eqpd"}
        for col in required:
            if col not in df_source.columns:
                missing_required.append(col)

        return {
            "file_name": uploaded_file.name,
            "total_rows": total_rows,
            "unique_tickets_in_file": unique_tickets_in_file,
            "duplicate_tickets_in_file": duplicate_tickets_in_file,
            "date_min": date_min,
            "date_max": date_max,
            "would_insert": would_insert,
            "would_update": would_update,
            "would_skip": would_skip,
            "missing_required": missing_required,
            "is_valid": len(missing_required) == 0,
        }

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def execute_uploaded_csv_load(uploaded_file: UploadedFile, load_type: str) -> dict[str, Any]:
    """
    Execute the selected CSV load and return final load statistics.
    """
    temp_path = save_uploaded_file_to_temp(uploaded_file)

    try:
        stats = process_csv_to_database(
            csv_path=temp_path,
            db_url=get_database_url(),
            load_type=load_type,
        )

        return {
            "file_name": uploaded_file.name,
            "total_rows": stats.total_rows,
            "inserted_rows": stats.inserted_rows,
            "updated_rows": stats.updated_rows,
            "skipped_rows": stats.skipped_rows,
            "error_rows": stats.error_rows,
        }

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def fetch_load_history(limit: int = 20) -> pd.DataFrame:
    """
    Return recent load-log history from the database.
    """
    engine = get_engine()

    sql = text(
        f"""
        SELECT
            load_id,
            file_name,
            load_type,
            started_at,
            ended_at,
            status,
            total_rows,
            inserted_rows,
            updated_rows,
            skipped_rows,
            error_rows,
            error_message
        FROM {LOAD_LOG_TABLE}
        ORDER BY load_id DESC
        LIMIT :limit
        """
    )

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})