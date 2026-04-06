import calendar

import pandas as pd

MONTH_LABELS = {
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

WEEK_BUCKETS = [
    (1, 7, "Semana 1 (1–7)"),
    (8, 15, "Semana 2 (8–15)"),
    (16, 22, "Semana 3 (16–22)"),
    (23, 31, "Semana 4 (23–31)"),
]

MONTH_ORDER = [MONTH_LABELS[i] for i in range(1, 13)]
WEEK_ORDER = [label for _, _, label in WEEK_BUCKETS]


def prepare_dates(frame: pd.DataFrame, column: str = "Date") -> pd.DataFrame:
    out = frame.copy()
    if column in out.columns:
        out[column] = pd.to_datetime(out[column], errors="coerce")
    return out


def normalize_transac(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.upper().str.strip()
    normalized = normalized.replace({"NAN": "OTROS", "NONE": "OTROS", "": "OTROS"})
    normalized = normalized.where(
        normalized.isin(["TKTT", "EMDA", "EMDS"]),
        "OTROS",
    )
    return normalized


def week_bucket(day: int) -> str:
    for start, end, label in WEEK_BUCKETS:
        if start <= int(day) <= end:
            return label
    return "Semana 4 (23–31)"


def month_label(month_number: int) -> str:
    return MONTH_LABELS.get(int(month_number), calendar.month_name[int(month_number)])