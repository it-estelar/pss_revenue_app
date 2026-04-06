import pandas as pd

from utils import safe_round


def build_emisor_route_matrix(coupons_long):
    if coupons_long.empty:
        return pd.DataFrame(columns=["Emisor"])

    pivot = pd.pivot_table(
        coupons_long,
        index="Emisor",
        columns="Ruta",
        values="Revenue",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    route_cols = [c for c in pivot.columns if c != "Emisor"]

    for col in route_cols:
        pivot[col] = pivot[col].apply(lambda x: safe_round(x, 0))

    pivot["TOTAL"] = pivot[route_cols].sum(axis=1).apply(lambda x: safe_round(x, 0))
    pivot = pivot.sort_values("TOTAL", ascending=False).reset_index(drop=True)

    total_row = {"Emisor": "TOTAL"}
    for col in route_cols:
        total_row[col] = int(pivot[col].sum())
    total_row["TOTAL"] = int(pivot["TOTAL"].sum())

    return pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)