from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


# ---------- DATAFRAME ----------

def dedupe_columns(columns) -> list[str]:
    seen = Counter()
    out = []

    for col in columns:
        clean = str(col).strip()
        seen[clean] += 1
        out.append(clean if seen[clean] == 1 else f"{clean}_{seen[clean]}")

    return out


# ---------- NUMERIC ----------

def to_numeric_series(series: pd.Series) -> pd.Series:
    s = (
        series.astype(str)
        .str.strip()
        .replace({"": "0", "None": "0", "nan": "0", "NULL": "0"})
        .str.replace(" ", "", regex=False)
        .str.replace("\u00a0", "", regex=False)
    )

    both_mask = s.str.contains(",", regex=False) & s.str.contains(".", regex=False)
    s.loc[both_mask] = (
        s.loc[both_mask]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    comma_only_mask = s.str.contains(",", regex=False) & ~s.str.contains(".", regex=False)
    s.loc[comma_only_mask] = s.loc[comma_only_mask].str.replace(",", ".", regex=False)

    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def format_money(value: Any, decimals: int = 2) -> str:
    try:
        formatted = f"{float(value):,.{decimals}f}"
    except Exception:
        formatted = f"{0:,.{decimals}f}"

    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def safe_round(value: Any, decimals: int = 0) -> float | int:
    try:
        return round(float(value), decimals)
    except Exception:
        return 0


# ---------- TEXT ----------

def clean_text(value: Any) -> str | None:
    txt = str(value).strip()
    if txt in {"", "nan", "None", "NULL"}:
        return None
    return txt


# ---------- ROUTES ----------

def normalize_route(origen: Any, destino: Any) -> str:
    o = str(origen).strip().upper().replace(" ", "")
    d = str(destino).strip().upper().replace(" ", "")

    if o in {"", "NAN", "NONE"} or d in {"", "NAN", "NONE"}:
        return ""

    return f"{o}-{d}" if o < d else f"{d}-{o}"