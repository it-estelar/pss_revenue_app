import pandas as pd

from utils import safe_round
from .helpers import MONTH_LABELS, WEEK_ORDER, month_label, normalize_transac, prepare_dates, week_bucket


def build_sales_monthly_report(df, selected_year: int):
    frame = prepare_dates(df, "Date")
    if frame.empty or "Date" not in frame.columns:
        return pd.DataFrame(columns=["Mes", "Revenue USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"])

    frame = frame[frame["Date"].dt.year == int(selected_year)].copy()
    if frame.empty:
        return pd.DataFrame(columns=["Mes", "Revenue USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"])

    frame["Transac_Normalizada"] = normalize_transac(frame["Transac"])
    frame["MesNum"] = frame["Date"].dt.month
    frame["Mes"] = frame["MesNum"].map(MONTH_LABELS)
    frame["Coupons Sold"] = pd.to_numeric(frame.get("Coupons Sold", 0), errors="coerce").fillna(0)
    frame["Revenue"] = pd.to_numeric(frame.get("Revenue", 0), errors="coerce").fillna(0)

    summary = (
        frame.groupby(["MesNum", "Mes"], as_index=False)
        .agg(
            **{
                "Revenue USD": ("Revenue", "sum"),
                "Cupones": ("Coupons Sold", "sum"),
            }
        )
    )

    counts = (
        frame.pivot_table(
            index=["MesNum", "Mes"],
            columns="Transac_Normalizada",
            values="Revenue",
            aggfunc="size",
            fill_value=0,
        )
        .reset_index()
    )

    out = summary.merge(counts, on=["MesNum", "Mes"], how="left")

    for col in ["TKTT", "EMDA", "EMDS", "OTROS"]:
        if col not in out.columns:
            out[col] = 0

    out = out.rename(columns={
        "TKTT": "TKTT #",
        "EMDA": "EMDA #",
        "EMDS": "EMDS #",
        "OTROS": "OTROS #",
    })

    out = out.sort_values("MesNum").reset_index(drop=True)
    out["Revenue USD"] = out["Revenue USD"].apply(lambda x: safe_round(x, 0))
    out["Cupones"] = out["Cupones"].apply(lambda x: int(safe_round(x, 0)))

    for col in ["TKTT #", "EMDA #", "EMDS #", "OTROS #"]:
        out[col] = out[col].astype(int)

    total_row = pd.DataFrame([{
        "MesNum": 13,
        "Mes": "TOTAL AÑO",
        "Revenue USD": int(out["Revenue USD"].sum()),
        "Cupones": int(out["Cupones"].sum()),
        "TKTT #": int(out["TKTT #"].sum()),
        "EMDA #": int(out["EMDA #"].sum()),
        "EMDS #": int(out["EMDS #"].sum()),
        "OTROS #": int(out["OTROS #"].sum()),
    }])

    out = pd.concat([out, total_row], ignore_index=True)
    return out[["Mes", "Revenue USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"]]


def build_sales_weekly_report(df, selected_year: int, selected_month: int):
    frame = prepare_dates(df, "Date")
    if frame.empty or "Date" not in frame.columns:
        return pd.DataFrame(columns=["Semana", "Ingreso USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"])

    frame = frame[
        (frame["Date"].dt.year == int(selected_year)) &
        (frame["Date"].dt.month == int(selected_month))
    ].copy()

    if frame.empty:
        return pd.DataFrame(columns=["Semana", "Ingreso USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"])

    frame["Transac_Normalizada"] = normalize_transac(frame["Transac"])
    frame["WeekBucket"] = frame["Date"].dt.day.apply(week_bucket)
    frame["WeekOrder"] = frame["WeekBucket"].map({label: idx for idx, label in enumerate(WEEK_ORDER, start=1)})
    frame["Coupons Sold"] = pd.to_numeric(frame.get("Coupons Sold", 0), errors="coerce").fillna(0)
    frame["Revenue"] = pd.to_numeric(frame.get("Revenue", 0), errors="coerce").fillna(0)

    summary = (
        frame.groupby(["WeekOrder", "WeekBucket"], as_index=False)
        .agg(
            **{
                "Ingreso USD": ("Revenue", "sum"),
                "Cupones": ("Coupons Sold", "sum"),
            }
        )
    )

    counts = (
        frame.pivot_table(
            index=["WeekOrder", "WeekBucket"],
            columns="Transac_Normalizada",
            values="Revenue",
            aggfunc="size",
            fill_value=0,
        )
        .reset_index()
    )

    out = summary.merge(counts, on=["WeekOrder", "WeekBucket"], how="left")

    for col in ["TKTT", "EMDA", "EMDS", "OTROS"]:
        if col not in out.columns:
            out[col] = 0

    out = out.rename(columns={
        "WeekBucket": "Semana",
        "TKTT": "TKTT #",
        "EMDA": "EMDA #",
        "EMDS": "EMDS #",
        "OTROS": "OTROS #",
    })

    out = out.sort_values("WeekOrder").reset_index(drop=True)
    out["Ingreso USD"] = out["Ingreso USD"].apply(lambda x: safe_round(x, 0))
    out["Cupones"] = out["Cupones"].apply(lambda x: int(safe_round(x, 0)))

    for col in ["TKTT #", "EMDA #", "EMDS #", "OTROS #"]:
        out[col] = out[col].astype(int)

    total_row = pd.DataFrame([{
        "WeekOrder": 99,
        "Semana": "TOTAL MES",
        "Ingreso USD": int(out["Ingreso USD"].sum()),
        "Cupones": int(out["Cupones"].sum()),
        "TKTT #": int(out["TKTT #"].sum()),
        "EMDA #": int(out["EMDA #"].sum()),
        "EMDS #": int(out["EMDS #"].sum()),
        "OTROS #": int(out["OTROS #"].sum()),
    }])

    out = pd.concat([out, total_row], ignore_index=True)
    return out[["Semana", "Ingreso USD", "Cupones", "TKTT #", "EMDA #", "EMDS #", "OTROS #"]]


def build_sales_route_month_report(coupons_long, selected_year: int):
    month_cols = [MONTH_LABELS[i] for i in range(1, 13)]

    if coupons_long is None or coupons_long.empty:
        return pd.DataFrame(columns=["Ruta", *month_cols, "TOTAL"])

    frame = prepare_dates(coupons_long, "Date")
    if frame.empty or "Date" not in frame.columns or "Ruta" not in frame.columns:
        return pd.DataFrame(columns=["Ruta", *month_cols, "TOTAL"])

    frame = frame[frame["Date"].dt.year == int(selected_year)].copy()
    if frame.empty:
        return pd.DataFrame(columns=["Ruta", *month_cols, "TOTAL"])

    frame["Ruta"] = frame["Ruta"].astype(str).str.strip().str.upper()
    frame["Revenue"] = pd.to_numeric(frame.get("Revenue", 0), errors="coerce").fillna(0)
    frame["MesNum"] = frame["Date"].dt.month

    frame = frame[
        (frame["Ruta"] != "")
        & (frame["Ruta"] != "NAN")
        & (frame["Ruta"] != "NONE")
    ].copy()

    if frame.empty:
        return pd.DataFrame(columns=["Ruta", *month_cols, "TOTAL"])

    pivot = (
        frame.pivot_table(
            index="Ruta",
            columns="MesNum",
            values="Revenue",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    for month_num in range(1, 13):
        if month_num not in pivot.columns:
            pivot[month_num] = 0

    pivot = pivot[["Ruta"] + list(range(1, 13))].copy()
    pivot = pivot.rename(columns={i: MONTH_LABELS[i] for i in range(1, 13)})

    for col in month_cols:
        pivot[col] = pivot[col].apply(lambda x: int(safe_round(x, 0)))

    pivot["TOTAL"] = pivot[month_cols].sum(axis=1).astype(int)
    pivot = pivot.sort_values("TOTAL", ascending=False).reset_index(drop=True)

    total_row = {"Ruta": "TOTAL"}
    for col in month_cols:
        total_row[col] = int(pivot[col].sum())
    total_row["TOTAL"] = int(pivot["TOTAL"].sum())

    pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)
    return pivot


def get_sales_available_years(df):
    frame = prepare_dates(df, "Date")
    if frame.empty or "Date" not in frame.columns:
        return []

    years = sorted(frame["Date"].dropna().dt.year.unique().tolist())
    return [int(y) for y in years]


def get_sales_available_months(df, selected_year: int):
    frame = prepare_dates(df, "Date")
    if frame.empty or "Date" not in frame.columns:
        return []

    frame = frame[frame["Date"].dt.year == int(selected_year)].copy()
    months = sorted(frame["Date"].dropna().dt.month.unique().tolist())

    return [{"value": int(m), "label": month_label(int(m))} for m in months]