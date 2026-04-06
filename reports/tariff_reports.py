import pandas as pd

from utils import safe_round


CLASS_COLUMNS = ["Clase_1", "Clase_2", "Clase_3", "Clase_4"]
COUPON_COLUMNS = ["Nro Cupon_1", "Nro Cupon_2", "Nro Cupon_3", "Nro Cupon_4"]
INVALID_CLASS_VALUES = {"", "NONE", "NAN", "NULL"}


def _normalize_currency_selection(selected_currency):
    if selected_currency is None:
        return []

    if isinstance(selected_currency, (list, tuple, set)):
        return [str(x).strip() for x in selected_currency if str(x).strip()]

    value = str(selected_currency).strip()
    return [value] if value else []


def _prepare_raw_tariff_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Moneda", "Clase", "Revenue_Asignado", "Nro Cupon"])

    work = df.copy()

    for col in ["Moneda", "Nro_Ticket"]:
        if col not in work.columns:
            work[col] = ""
        work[col] = work[col].fillna("").astype(str).str.strip()

    work["Moneda"] = work["Moneda"].str.upper()
    work["Revenue"] = pd.to_numeric(work.get("Revenue", 0), errors="coerce").fillna(0.0)
    work["Coupons Sold"] = pd.to_numeric(work.get("Coupons Sold", 0), errors="coerce").fillna(0).astype(int)

    for col in CLASS_COLUMNS + COUPON_COLUMNS:
        if col not in work.columns:
            work[col] = ""
        work[col] = work[col].fillna("").astype(str).str.strip()

    for col in CLASS_COLUMNS:
        work[col] = work[col].str.upper()

    rows = []

    for _, row in work.iterrows():
        class_values = [str(row[c]).strip().upper() for c in CLASS_COLUMNS]
        coupon_values = [str(row[c]).strip() for c in COUPON_COLUMNS]

        valid_classes = [c for c in class_values if c not in INVALID_CLASS_VALUES]
        valid_class_count = len(valid_classes)

        if valid_class_count <= 0:
            # Keep revenue visible instead of losing it.
            rows.append(
                {
                    "Moneda": row["Moneda"] if str(row["Moneda"]).strip() else "SIN MONEDA",
                    "Clase": "EMDS Y EMDA",
                    "Revenue_Asignado": float(row["Revenue"]),
                    "Nro Cupon": "SIN CUPON",
                }
            )
            continue

        revenue_per_coupon = float(row["Revenue"]) / valid_class_count if valid_class_count > 0 else float(row["Revenue"])

        for i in range(4):
            clase = class_values[i]
            cupon = coupon_values[i]

            if clase in INVALID_CLASS_VALUES:
                continue

            rows.append(
                {
                    "Moneda": row["Moneda"] if str(row["Moneda"]).strip() else "SIN MONEDA",
                    "Clase": clase,
                    "Revenue_Asignado": revenue_per_coupon,
                    "Nro Cupon": cupon if cupon else f"CUPON_{i+1}",
                }
            )

    return pd.DataFrame(rows)


def build_revenue_by_currency_class(df):
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "Moneda",
                "Clase",
                "Monto_USD",
                "Cantidad_de_Cupones",
                "Valor_de_la_Tarifa",
            ]
        )

    exploded = _prepare_raw_tariff_rows(df)

    if exploded.empty:
        return pd.DataFrame(
            columns=[
                "Moneda",
                "Clase",
                "Monto_USD",
                "Cantidad_de_Cupones",
                "Valor_de_la_Tarifa",
            ]
        )

    grouped = (
        exploded.groupby(["Moneda", "Clase"], dropna=False, as_index=False)
        .agg(
            Monto_USD=("Revenue_Asignado", "sum"),
            Cantidad_de_Cupones=("Nro Cupon", "count"),
        )
        .sort_values(["Moneda", "Monto_USD"], ascending=[True, False])
        .reset_index(drop=True)
    )

    grouped["Moneda"] = grouped["Moneda"].astype(str).str.strip()
    grouped["Clase"] = grouped["Clase"].fillna("").astype(str).str.strip()

    grouped["Monto_USD"] = grouped["Monto_USD"].apply(lambda x: safe_round(x, 0))
    grouped["Cantidad_de_Cupones"] = grouped["Cantidad_de_Cupones"].astype(int)
    grouped["Valor_de_la_Tarifa"] = (
        grouped["Monto_USD"] / grouped["Cantidad_de_Cupones"]
    ).replace([float("inf"), -float("inf")], 0).fillna(0).apply(lambda x: safe_round(x, 0))

    total_row = pd.DataFrame(
        [{
            "Moneda": "TOTAL",
            "Clase": "",
            "Monto_USD": int(grouped["Monto_USD"].sum()),
            "Cantidad_de_Cupones": int(grouped["Cantidad_de_Cupones"].sum()),
            "Valor_de_la_Tarifa": "",
        }]
    )

    return pd.concat([grouped, total_row], ignore_index=True)


def build_tariff_style_report(revenue_by_currency_class, selected_currency=None):
    frame = revenue_by_currency_class.copy()

    if frame.empty:
        return pd.DataFrame(
            columns=[
                "MONEDA",
                "CLASE TARIFARIA",
                "VALOR DE LA TARIFA",
                "MONTO USD",
                "CANTIDAD DE CUPONES",
                "% DEL TOTAL",
            ]
        )

    frame["Moneda"] = frame["Moneda"].astype(str).str.strip()
    frame["Clase"] = frame["Clase"].fillna("").astype(str).str.strip()
    frame = frame[frame["Moneda"].str.upper() != "TOTAL"].copy()

    selected_currencies = _normalize_currency_selection(selected_currency)
    if selected_currencies:
        frame = frame[frame["Moneda"].isin(selected_currencies)].copy()

    if frame.empty:
        return pd.DataFrame(
            columns=[
                "MONEDA",
                "CLASE TARIFARIA",
                "VALOR DE LA TARIFA",
                "MONTO USD",
                "CANTIDAD DE CUPONES",
                "% DEL TOTAL",
            ]
        )

    total_usd = frame["Monto_USD"].sum()

    out = frame.rename(
        columns={
            "Moneda": "MONEDA",
            "Clase": "CLASE TARIFARIA",
            "Valor_de_la_Tarifa": "VALOR DE LA TARIFA",
            "Monto_USD": "MONTO USD",
            "Cantidad_de_Cupones": "CANTIDAD DE CUPONES",
        }
    ).copy()

    out["% DEL TOTAL"] = (
        out["MONTO USD"] / total_usd * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0).apply(lambda x: safe_round(x, 1))

    out = out.sort_values(["MONEDA", "MONTO USD"], ascending=[True, False]).reset_index(drop=True)

    total_row = pd.DataFrame([{
        "MONEDA": "TOTAL",
        "CLASE TARIFARIA": "",
        "VALOR DE LA TARIFA": "",
        "MONTO USD": int(out["MONTO USD"].sum()),
        "CANTIDAD DE CUPONES": int(out["CANTIDAD DE CUPONES"].sum()),
        "% DEL TOTAL": 100.0 if len(out) else 0.0,
    }])

    return pd.concat([out, total_row], ignore_index=True)