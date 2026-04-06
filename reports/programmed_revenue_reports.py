from __future__ import annotations

"""
Programmed Revenue and Volado report builders.

Responsibilities
----------------
- Reconstruct coupon-level rows from raw ticket-slot columns
- Allocate TKTT revenue across valid coupon rows
- Allocate EMDA revenue against the related TKTT document
- Build the programmed-revenue detail and summary payloads
- Build the Volado-by-route summary from the same reconstruction rules

Important
---------
This file is business-logic heavy.
Do not move Streamlit rendering or UI controls here.
"""

import pandas as pd

from utils import normalize_route, to_numeric_series


MONTH_NAMES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def _safe_string_column(df: pd.DataFrame, col_name: str, default: str = "") -> pd.Series:
    """
    Return a cleaned string column if present, otherwise a default-filled Series.
    """
    if col_name in df.columns:
        return df[col_name].astype(str).str.strip()
    return pd.Series([default] * len(df), index=df.index, dtype="object")


def _pick_revenue_column(df: pd.DataFrame) -> str:
    """
    Pick the first revenue-like column supported by this module.
    """
    candidates = [
        "Revenue",
        "MONTO USD",
        "Monto USD",
        "revenue_total",
        "(F_FA) Tarifa",
    ]
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError("No se encontró una columna de revenue utilizable.")


def _coupon_column_candidates(base_name: str, slot_idx: int) -> list[str]:
    """
    Soporta ambos esquemas:
    - cupón 1: Origen / Destino / Vuelo / Clase / Fecha Programada de vuelo
    - cupón 2+: Origen.1 / Destino.1 ...  o  Origen_2 / Destino_2 ...
    """
    if slot_idx == 1:
        return [base_name, f"{base_name}_1"]

    dot_suffix = slot_idx - 1
    return [
        f"{base_name}.{dot_suffix}",
        f"{base_name}_{slot_idx}",
    ]


def _row_value(row: pd.Series, candidates: list[str]):
    """
    Return the first usable value found among a list of candidate columns.
    """
    for col in candidates:
        if col in row.index:
            val = row.get(col)
            if pd.notna(val) and str(val).strip() != "":
                return val
    return None


def _build_ticket_coupon_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand raw TKTT ticket rows into coupon-level rows and split revenue evenly
    across the valid coupons found for each document.
    """
    base_cols = [
        "ticket",
        "transac",
        "related_doc",
        "coupon_number",
        "fecha_prog",
        "vuelo",
        "origen",
        "destino",
        "ruta",
        "clase",
        "emisor",
        "pax",
        "cod_reserva",
        "foid",
        "fbasis",
        "source_doc",
        "coupon_count",
        "assigned_revenue",
    ]

    if df.empty:
        return pd.DataFrame(columns=base_cols)

    revenue_col = _pick_revenue_column(df)

    work = df.copy()
    work["Nro_Ticket"] = _safe_string_column(work, "Nro_Ticket")
    work["Transac"] = _safe_string_column(work, "Transac").str.upper()
    work["Related_Doc"] = _safe_string_column(work, "Related_Doc")
    work["Emisor"] = _safe_string_column(work, "Emisor")
    work["Pax"] = _safe_string_column(work, "Pax")
    work["Cod_Reserva"] = _safe_string_column(work, "Cod_Reserva")
    work["FOID"] = _safe_string_column(work, "FOID")
    work["_revenue_value"] = to_numeric_series(work[revenue_col]).fillna(0.0)

    exploded_rows = []

    for _, row in work.iterrows():
        coupon_rows = []

        for slot_idx in range(1, 5):
            origen = _row_value(row, _coupon_column_candidates("Origen", slot_idx))
            destino = _row_value(row, _coupon_column_candidates("Destino", slot_idx))
            vuelo = _row_value(row, _coupon_column_candidates("Vuelo", slot_idx))
            clase = _row_value(row, _coupon_column_candidates("Clase", slot_idx))
            fecha_prog = _row_value(row, _coupon_column_candidates("Fecha Programada de vuelo", slot_idx))

            fbasis_col = f"FBasisCupon{slot_idx}"
            fbasis = row.get(fbasis_col) if fbasis_col in row.index else ""

            # si no hay fecha, este cupón no se usa
            if pd.isna(fecha_prog) or str(fecha_prog).strip() == "":
                continue

            route_norm = normalize_route(origen, destino)
            if not route_norm:
                continue

            coupon_rows.append(
                {
                    "ticket": row["Nro_Ticket"],
                    "transac": row["Transac"],
                    "related_doc": row.get("Related_Doc", ""),
                    "coupon_number": slot_idx,
                    "fecha_prog": pd.to_datetime(fecha_prog, errors="coerce"),
                    "vuelo": str(vuelo).strip() if pd.notna(vuelo) and vuelo is not None else "",
                    "origen": str(origen).strip().upper() if pd.notna(origen) and origen is not None else "",
                    "destino": str(destino).strip().upper() if pd.notna(destino) and destino is not None else "",
                    "ruta": route_norm,
                    "clase": str(clase).strip().upper() if pd.notna(clase) and clase is not None else "",
                    "emisor": str(row.get("Emisor", "")).strip(),
                    "pax": str(row.get("Pax", "")).strip(),
                    "cod_reserva": str(row.get("Cod_Reserva", "")).strip(),
                    "foid": str(row.get("FOID", "")).strip(),
                    "fbasis": str(fbasis).strip().upper() if pd.notna(fbasis) else "",
                    "source_doc": row["Nro_Ticket"],
                }
            )

        coupon_count = len(coupon_rows)
        if coupon_count == 0:
            continue

        assigned = float(row["_revenue_value"]) / coupon_count

        for c in coupon_rows:
            c["coupon_count"] = coupon_count
            c["assigned_revenue"] = assigned
            exploded_rows.append(c)

    if not exploded_rows:
        return pd.DataFrame(columns=base_cols)

    out = pd.DataFrame(exploded_rows)
    out["fecha_prog"] = pd.to_datetime(out["fecha_prog"], errors="coerce")
    return out


def _build_emda_allocations(df: pd.DataFrame, tktt_coupon_rows: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Allocate EMDA revenue to the coupon rows of the related TKTT document.
    """
    if df.empty:
        return pd.DataFrame(columns=tktt_coupon_rows.columns), 0

    revenue_col = _pick_revenue_column(df)

    work = df.copy()
    work["Nro_Ticket"] = _safe_string_column(work, "Nro_Ticket")
    work["Transac"] = _safe_string_column(work, "Transac").str.upper()
    work["Related_Doc"] = _safe_string_column(work, "Related_Doc")
    work["Emisor"] = _safe_string_column(work, "Emisor")
    work["_revenue_value"] = to_numeric_series(work[revenue_col]).fillna(0.0)

    emda_rows = work[work["Transac"] == "EMDA"].copy()

    if emda_rows.empty or tktt_coupon_rows.empty:
        return pd.DataFrame(columns=tktt_coupon_rows.columns), int(len(emda_rows))

    related_map = {
        ticket: grp.copy()
        for ticket, grp in tktt_coupon_rows.groupby("ticket", dropna=False)
    }

    alloc_rows = []
    unmatched = 0

    for _, row in emda_rows.iterrows():
        related_doc = row["Related_Doc"]

        if not related_doc or related_doc not in related_map:
            unmatched += 1
            continue

        related_coupons = related_map[related_doc]
        coupon_count = len(related_coupons)

        if coupon_count == 0:
            unmatched += 1
            continue

        assigned = float(row["_revenue_value"]) / coupon_count

        for _, rc in related_coupons.iterrows():
            alloc_rows.append(
                {
                    "ticket": related_doc,
                    "transac": "EMDA",
                    "related_doc": related_doc,
                    "coupon_number": rc["coupon_number"],
                    "fecha_prog": rc["fecha_prog"],
                    "vuelo": rc["vuelo"],
                    "origen": rc["origen"],
                    "destino": rc["destino"],
                    "ruta": rc["ruta"],
                    "clase": rc["clase"],
                    "emisor": str(row.get("Emisor", "")).strip(),
                    "pax": rc["pax"],
                    "cod_reserva": rc["cod_reserva"],
                    "foid": rc["foid"],
                    "fbasis": rc["fbasis"],
                    "source_doc": row["Nro_Ticket"],
                    "coupon_count": coupon_count,
                    "assigned_revenue": assigned,
                }
            )

    if not alloc_rows:
        return pd.DataFrame(columns=tktt_coupon_rows.columns), unmatched

    out = pd.DataFrame(alloc_rows)
    out["fecha_prog"] = pd.to_datetime(out["fecha_prog"], errors="coerce")
    return out, unmatched


def get_programmed_revenue_filter_options(df: pd.DataFrame) -> dict:
    """
    Build the available route, year, and month filters from TKTT coupon rows.
    """
    if df.empty or "Transac" not in df.columns:
        return {"routes": [], "years": [], "months": []}

    tktt_mask = df["Transac"].astype(str).str.upper() == "TKTT"
    tktt_coupon_rows = _build_ticket_coupon_rows(df[tktt_mask].copy())

    if tktt_coupon_rows.empty:
        return {"routes": [], "years": [], "months": []}

    valid = tktt_coupon_rows.dropna(subset=["fecha_prog"]).copy()
    valid["year"] = valid["fecha_prog"].dt.year
    valid["month"] = valid["fecha_prog"].dt.month

    routes = sorted(valid["ruta"].dropna().astype(str).unique().tolist())
    years = sorted(valid["year"].dropna().astype(int).unique().tolist())
    months = sorted(valid["month"].dropna().astype(int).unique().tolist())

    return {"routes": routes, "years": years, "months": months}


def build_programmed_revenue_outputs(df: pd.DataFrame, route: str, month: int, year: int) -> dict:
    """
    Build the detail table, summary table, and validation block for the
    Programmed Revenue module.
    """
    empty_validation = {
        "total_tktt_coupon_rows": 0,
        "total_emda_allocated_rows": 0,
        "unmatched_emda": 0,
        "documents_in_scope": 0,
        "month_name": MONTH_NAMES.get(month, str(month)),
    }

    if df.empty or "Transac" not in df.columns:
        return {
            "detail": pd.DataFrame(),
            "summary": pd.DataFrame(),
            "validation": empty_validation,
        }

    work = df.copy()
    work["Transac"] = work["Transac"].astype(str).str.upper()

    tktt_coupon_rows = _build_ticket_coupon_rows(work[work["Transac"] == "TKTT"].copy())
    emda_allocations, unmatched_emda = _build_emda_allocations(work, tktt_coupon_rows)

    full_detail = pd.concat([tktt_coupon_rows, emda_allocations], ignore_index=True)

    if full_detail.empty:
        return {
            "detail": pd.DataFrame(),
            "summary": pd.DataFrame(),
            "validation": {
                **empty_validation,
                "unmatched_emda": int(unmatched_emda),
            },
        }

    full_detail = full_detail.dropna(subset=["fecha_prog"]).copy()
    full_detail["year"] = full_detail["fecha_prog"].dt.year
    full_detail["month"] = full_detail["fecha_prog"].dt.month

    filtered = full_detail[
        (full_detail["ruta"].astype(str) == str(route))
        & (full_detail["year"] == int(year))
        & (full_detail["month"] == int(month))
    ].copy()

    if filtered.empty:
        return {
            "detail": pd.DataFrame(),
            "summary": pd.DataFrame(),
            "validation": {
                **empty_validation,
                "total_tktt_coupon_rows": int(len(tktt_coupon_rows)),
                "total_emda_allocated_rows": int(len(emda_allocations)),
                "unmatched_emda": int(unmatched_emda),
            },
        }

    summary = (
        filtered.groupby(["fecha_prog", "origen", "destino", "vuelo"], dropna=False)
        .agg(
            Cupones=("ticket", "count"),
            Tickets=("ticket", pd.Series.nunique),
            Ingreso=("assigned_revenue", "sum"),
        )
        .reset_index()
        .sort_values(["fecha_prog", "origen", "destino", "vuelo"])
        .reset_index(drop=True)
    )

    tktt_summary = (
        filtered[filtered["transac"] == "TKTT"]
        .groupby(["fecha_prog", "origen", "destino", "vuelo"], dropna=False)["assigned_revenue"]
        .sum()
        .reset_index(name="TKTT_Ingreso")
    )

    emda_summary = (
        filtered[filtered["transac"] == "EMDA"]
        .groupby(["fecha_prog", "origen", "destino", "vuelo"], dropna=False)["assigned_revenue"]
        .sum()
        .reset_index(name="EMDA_Ingreso")
    )

    summary = summary.merge(
        tktt_summary,
        on=["fecha_prog", "origen", "destino", "vuelo"],
        how="left",
    )
    summary = summary.merge(
        emda_summary,
        on=["fecha_prog", "origen", "destino", "vuelo"],
        how="left",
    )

    summary["TKTT_Ingreso"] = summary["TKTT_Ingreso"].fillna(0.0)
    summary["EMDA_Ingreso"] = summary["EMDA_Ingreso"].fillna(0.0)
    summary["fecha_prog"] = summary["fecha_prog"].dt.strftime("%Y-%m-%d")

    detail_cols = [
        "fecha_prog",
        "origen",
        "destino",
        "vuelo",
        "ticket",
        "transac",
        "source_doc",
        "clase",
        "emisor",
        "coupon_number",
        "coupon_count",
        "assigned_revenue",
        "pax",
        "cod_reserva",
        "foid",
    ]

    detail = filtered[detail_cols].copy()
    detail["fecha_prog"] = detail["fecha_prog"].dt.strftime("%Y-%m-%d")
    detail = detail.sort_values(["fecha_prog", "vuelo", "ticket", "transac"]).reset_index(drop=True)

    validation = {
        "total_tktt_coupon_rows": int(len(tktt_coupon_rows)),
        "total_emda_allocated_rows": int(len(emda_allocations)),
        "unmatched_emda": int(unmatched_emda),
        "documents_in_scope": int(filtered["ticket"].nunique()),
        "month_name": MONTH_NAMES.get(month, str(month)),
    }

    return {
        "detail": detail,
        "summary": summary,
        "validation": validation,
    }


def build_volado_by_route_report(df: pd.DataFrame, date_from=None, date_to=None) -> pd.DataFrame:
    """
    Build the Volado-by-route report using the same coupon reconstruction and
    EMDA allocation rules as Programmed Revenue.
    """
    if df.empty or "Transac" not in df.columns:
        return pd.DataFrame(columns=["Ruta", "Ingreso USD", "Cupones", "Tickets"])

    tktt_mask = df["Transac"].astype(str).str.upper() == "TKTT"
    tktt_coupon_rows = _build_ticket_coupon_rows(df[tktt_mask].copy())
    emda_allocations, _ = _build_emda_allocations(df, tktt_coupon_rows)

    combined = pd.concat([tktt_coupon_rows, emda_allocations], ignore_index=True)

    if combined.empty:
        return pd.DataFrame(columns=["Ruta", "Ingreso USD", "Cupones", "Tickets"])

    combined["fecha_prog"] = pd.to_datetime(combined["fecha_prog"], errors="coerce")

    if date_from is not None:
        combined = combined[combined["fecha_prog"] >= pd.to_datetime(date_from)]
    if date_to is not None:
        combined = combined[combined["fecha_prog"] <= pd.to_datetime(date_to)]

    if combined.empty:
        return pd.DataFrame(columns=["Ruta", "Ingreso USD", "Cupones", "Tickets"])

    out = (
        combined.groupby("ruta", dropna=False)
        .agg(
            **{
                "Ingreso USD": ("assigned_revenue", "sum"),
                "Cupones": ("ticket", "count"),
                "Tickets": ("ticket", pd.Series.nunique),
            }
        )
        .reset_index()
        .rename(columns={"ruta": "Ruta"})
        .sort_values("Ingreso USD", ascending=False)
        .reset_index(drop=True)
    )

    total_row = pd.DataFrame(
        [
            {
                "Ruta": "TOTAL",
                "Ingreso USD": float(out["Ingreso USD"].sum()),
                "Cupones": int(out["Cupones"].sum()),
                "Tickets": int(out["Tickets"].sum()),
            }
        ]
    )

    return pd.concat([out, total_row], ignore_index=True)