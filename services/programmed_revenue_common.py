from __future__ import annotations

import pandas as pd


MESES = {
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


def fmt_flight(value) -> str:
    txt = str(value).strip()
    if txt in {"", "nan", "None"}:
        return ""
    digits = "".join(ch for ch in txt if ch.isdigit())
    if digits:
        return str(int(digits)).zfill(4)
    return txt


def normalize_summary_for_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if "vuelo" in out.columns:
        out["vuelo"] = out["vuelo"].map(fmt_flight)

    group_cols = ["fecha_prog", "origen", "destino", "vuelo"]
    numeric_cols = ["Cupones", "Tickets", "Ingreso", "TKTT_Ingreso", "EMDA_Ingreso"]

    for col in group_cols:
        if col not in out.columns:
            out[col] = ""

    for col in numeric_cols:
        if col not in out.columns:
            out[col] = 0

    out = (
        out.groupby(group_cols, dropna=False)[numeric_cols]
        .sum()
        .reset_index()
        .sort_values(group_cols)
        .reset_index(drop=True)
    )

    return out