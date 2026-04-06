import pandas as pd

from utils import safe_round


def _clean_emisor_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Emisor"] = out["Emisor"].fillna("").astype(str).str.strip()
    out.loc[out["Emisor"] == "", "Emisor"] = "SIN EMISOR"
    return out


def _clean_coupon_emisor_route_columns(coupons_long: pd.DataFrame) -> pd.DataFrame:
    out = coupons_long.copy()

    out["Emisor"] = out["Emisor"].fillna("").astype(str).str.strip()
    out.loc[out["Emisor"] == "", "Emisor"] = "SIN EMISOR"

    out["Ruta"] = out["Ruta"].fillna("").astype(str).str.strip().str.upper()
    out.loc[out["Ruta"] == "", "Ruta"] = "SIN RUTA"

    out["Revenue"] = pd.to_numeric(out["Revenue"], errors="coerce").fillna(0)

    return out


def get_emisor_filter_options(coupons_long: pd.DataFrame):
    if coupons_long is None or coupons_long.empty or "Emisor" not in coupons_long.columns:
        return []

    work = _clean_coupon_emisor_route_columns(coupons_long)

    values = work["Emisor"].dropna().astype(str).str.strip()
    values = values[values != ""].drop_duplicates()

    return sorted(values.tolist(), key=lambda x: x.upper())


def build_revenue_by_emisor(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Posicion", "Emisor", "Revenue", "Cantidad_de_Cupones"])

    work = _clean_emisor_column(df)

    out = (
        work.groupby("Emisor", dropna=False, as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Cantidad_de_Cupones=("Coupons Sold", "sum"),
        )
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )

    out["Revenue"] = out["Revenue"].apply(lambda x: safe_round(x, 0))
    out["Cantidad_de_Cupones"] = out["Cantidad_de_Cupones"].apply(lambda x: int(safe_round(x, 0)))
    out.insert(0, "Posicion", range(1, len(out) + 1))

    total_row = pd.DataFrame([{
        "Posicion": "",
        "Emisor": "TOTAL",
        "Revenue": int(out["Revenue"].sum()),
        "Cantidad_de_Cupones": int(out["Cantidad_de_Cupones"].sum()),
    }])

    return pd.concat([out, total_row], ignore_index=True)


def build_routes_by_emisor(coupons_long: pd.DataFrame, selected_emisores=None):
    if coupons_long is None or coupons_long.empty:
        return pd.DataFrame(columns=["Posicion", "Ruta", "Revenue", "Cantidad_de_Cupones"])

    work = _clean_coupon_emisor_route_columns(coupons_long)

    selected_emisores = [str(x).strip() for x in (selected_emisores or []) if str(x).strip()]
    if selected_emisores:
        work = work[work["Emisor"].isin(selected_emisores)].copy()

    if work.empty:
        return pd.DataFrame(columns=["Posicion", "Ruta", "Revenue", "Cantidad_de_Cupones"])

    coupon_col = "Nro Cupon" if "Nro Cupon" in work.columns else None

    if coupon_col:
        out = (
            work.groupby("Ruta", dropna=False, as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Cantidad_de_Cupones=(coupon_col, "count"),
            )
            .sort_values("Revenue", ascending=False)
            .reset_index(drop=True)
        )
    else:
        out = (
            work.groupby("Ruta", dropna=False, as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Cantidad_de_Cupones=("Ruta", "count"),
            )
            .sort_values("Revenue", ascending=False)
            .reset_index(drop=True)
        )

    out["Revenue"] = out["Revenue"].apply(lambda x: safe_round(x, 0))
    out["Cantidad_de_Cupones"] = out["Cantidad_de_Cupones"].apply(lambda x: int(safe_round(x, 0)))
    out.insert(0, "Posicion", range(1, len(out) + 1))

    total_row = pd.DataFrame([{
        "Posicion": "",
        "Ruta": "TOTAL",
        "Revenue": int(out["Revenue"].sum()),
        "Cantidad_de_Cupones": int(out["Cantidad_de_Cupones"].sum()),
    }])

    return pd.concat([out, total_row], ignore_index=True)