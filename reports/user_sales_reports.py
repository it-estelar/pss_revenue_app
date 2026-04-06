import pandas as pd


def _norm_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )


def build_user_sales_base(df: pd.DataFrame, catalog_df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()

    for col in ["Agente Emisor", "Emisor", "Nro_Ticket"]:
        if col not in work.columns:
            work[col] = ""
        work[col] = work[col].fillna("").astype(str).str.strip()

    work["Revenue"] = pd.to_numeric(work.get("Revenue", 0), errors="coerce").fillna(0.0)
    work["Coupons Sold"] = pd.to_numeric(work.get("Coupons Sold", 0), errors="coerce").fillna(0).astype(int)
    work["Date"] = pd.to_datetime(work.get("Date"), errors="coerce")

    work["agente_emisor_key"] = _norm_text(work["Agente Emisor"])

    if catalog_df is None or catalog_df.empty:
        work["usuario"] = None
        work["agente_catalogo"] = None
        work["estacion"] = None
        return work

    cat = catalog_df.copy()
    for col in ["usuario", "agente", "estacion"]:
        if col not in cat.columns:
            cat[col] = ""
        cat[col] = cat[col].fillna("").astype(str).str.strip()

    if "activo" in cat.columns:
        cat = cat[cat["activo"].fillna(False) == True].copy()

    cat["usuario_key"] = _norm_text(cat["usuario"])

    cat = cat.drop_duplicates(subset=["usuario_key"], keep="first").copy()

    merged = work.merge(
        cat[["usuario_key", "usuario", "agente", "estacion"]],
        left_on="agente_emisor_key",
        right_on="usuario_key",
        how="left",
    )

    merged = merged.rename(
        columns={
            "agente": "agente_catalogo",
        }
    )

    return merged


def filter_user_sales_base(base_df: pd.DataFrame, selected_users: list[str] | None):
    if base_df is None or base_df.empty:
        return pd.DataFrame()

    work = base_df.copy()
    work = work[work["usuario"].notna()].copy()

    if selected_users:
        selected_keys = {str(x).strip().upper() for x in selected_users if str(x).strip()}
        work = work[
            work["usuario"].fillna("").astype(str).str.strip().str.upper().isin(selected_keys)
        ].copy()

    return work


def build_user_summary(base_df: pd.DataFrame) -> pd.DataFrame:
    if base_df is None or base_df.empty:
        return pd.DataFrame(
            columns=["USUARIO", "AGENTE", "ESTACION", "REVENUE", "TICKETS", "CUPONES"]
        )

    out = (
        base_df.groupby(["usuario", "agente_catalogo", "estacion"], dropna=False, as_index=False)
        .agg(
            REVENUE=("Revenue", "sum"),
            TICKETS=("Nro_Ticket", lambda s: s.astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
            CUPONES=("Coupons Sold", "sum"),
        )
        .rename(
            columns={
                "usuario": "USUARIO",
                "agente_catalogo": "AGENTE",
                "estacion": "ESTACION",
            }
        )
        .sort_values("REVENUE", ascending=False)
        .reset_index(drop=True)
    )

    out["AGENTE"] = out["AGENTE"].fillna("").astype(str)
    out["ESTACION"] = out["ESTACION"].fillna("").astype(str)
    return out


def build_user_monthly(base_df: pd.DataFrame) -> pd.DataFrame:
    if base_df is None or base_df.empty:
        return pd.DataFrame(columns=["MES", "USUARIO", "REVENUE", "TICKETS", "CUPONES"])

    work = base_df.copy()
    work = work[work["Date"].notna()].copy()

    if work.empty:
        return pd.DataFrame(columns=["MES", "USUARIO", "REVENUE", "TICKETS", "CUPONES"])

    work["month_period"] = work["Date"].dt.to_period("M")
    work["MES"] = work["month_period"].astype(str)

    out = (
        work.groupby(["MES", "usuario"], dropna=False, as_index=False)
        .agg(
            REVENUE=("Revenue", "sum"),
            TICKETS=("Nro_Ticket", lambda s: s.astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
            CUPONES=("Coupons Sold", "sum"),
        )
        .rename(columns={"usuario": "USUARIO"})
        .sort_values(["MES", "REVENUE"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return out


def build_user_emisor(base_df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    if base_df is None or base_df.empty:
        return pd.DataFrame(columns=["EMISOR", "REVENUE", "TICKETS", "CUPONES"])

    work = base_df.copy()
    work["Emisor"] = work["Emisor"].fillna("").astype(str).str.strip()
    work.loc[work["Emisor"] == "", "Emisor"] = "SIN EMISOR"

    out = (
        work.groupby("Emisor", dropna=False, as_index=False)
        .agg(
            REVENUE=("Revenue", "sum"),
            TICKETS=("Nro_Ticket", lambda s: s.astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
            CUPONES=("Coupons Sold", "sum"),
        )
        .rename(columns={"Emisor": "EMISOR"})
        .sort_values("REVENUE", ascending=False)
        .reset_index(drop=True)
    )

    return out.head(top_n).copy()