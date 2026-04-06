import pandas as pd

from utils import safe_round


def _normalize_route_selection(selected_route):
    if selected_route is None:
        return []
    if isinstance(selected_route, (list, tuple, set)):
        return [str(x).strip() for x in selected_route if str(x).strip()]
    value = str(selected_route).strip()
    return [value] if value else []


def _filter_by_selected_routes(coupons_long, selected_route):
    if coupons_long is None or coupons_long.empty:
        return pd.DataFrame()

    selected_routes = _normalize_route_selection(selected_route)

    # Si no se selecciona ninguna ruta, usar todas
    if not selected_routes:
        return coupons_long.copy()

    return coupons_long[coupons_long["Ruta"].astype(str).isin(selected_routes)].copy()


def build_route_emisor_report(coupons_long, selected_route):
    frame = _filter_by_selected_routes(coupons_long, selected_route)

    if frame.empty:
        return pd.DataFrame(columns=["Posicion", "Emisor", "Revenue", "Cantidad_de_Cupones"])

    out = (
        frame.groupby("Emisor", dropna=False, as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Cantidad_de_Cupones=("Nro Cupon", "count"),
        )
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )

    out["Revenue"] = out["Revenue"].apply(lambda x: safe_round(x, 0))
    out["Cantidad_de_Cupones"] = out["Cantidad_de_Cupones"].astype(int)
    out.insert(0, "Posicion", range(1, len(out) + 1))

    total_row = pd.DataFrame([{
        "Posicion": "",
        "Emisor": "TOTAL",
        "Revenue": int(out["Revenue"].sum()),
        "Cantidad_de_Cupones": int(out["Cantidad_de_Cupones"].sum()),
    }])

    return pd.concat([out, total_row], ignore_index=True)

def build_route_class_report(coupons_long, selected_route):
    frame = _filter_by_selected_routes(coupons_long, selected_route)

    if frame.empty:
        return pd.DataFrame(columns=["Clase", "Cantidad_de_Cupones"])

    work = frame.copy()
    work["Clase"] = work["Clase"].fillna("").astype(str).str.strip().str.upper()

    # Excluir clases vacías o marcadas como NONE
    work = work[~work["Clase"].isin(["", "NONE", "NAN", "NULL"])].copy()

    if work.empty:
        return pd.DataFrame(columns=["Clase", "Cantidad_de_Cupones"])

    out = (
        work.groupby("Clase", dropna=False, as_index=False)
        .agg(Cantidad_de_Cupones=("Nro Cupon", "count"))
        .sort_values("Cantidad_de_Cupones", ascending=False)
        .reset_index(drop=True)
    )

    out["Cantidad_de_Cupones"] = out["Cantidad_de_Cupones"].astype(int)

    total_row = pd.DataFrame([{
        "Clase": "TOTAL",
        "Cantidad_de_Cupones": int(out["Cantidad_de_Cupones"].sum()),
    }])

    return pd.concat([out, total_row], ignore_index=True)

def build_yield_by_route(coupons_long):
    if coupons_long.empty:
        return pd.DataFrame(columns=["Ruta", "Revenue", "Cantidad_de_Cupones", "Yield"])

    out = (
        coupons_long.groupby("Ruta", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Cantidad_de_Cupones=("Nro Cupon", "count"),
        )
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )

    out["Yield"] = (
        out["Revenue"] / out["Cantidad_de_Cupones"]
    ).replace([float("inf"), -float("inf")], 0).fillna(0)

    out["Revenue"] = out["Revenue"].apply(lambda x: safe_round(x, 0))
    out["Cantidad_de_Cupones"] = out["Cantidad_de_Cupones"].astype(int)
    out["Yield"] = out["Yield"].apply(lambda x: safe_round(x, 0))

    total_row = pd.DataFrame([{
        "Ruta": "TOTAL",
        "Revenue": int(out["Revenue"].sum()),
        "Cantidad_de_Cupones": int(out["Cantidad_de_Cupones"].sum()),
        "Yield": safe_round(
            out["Revenue"].sum() / out["Cantidad_de_Cupones"].sum(), 0
        ) if out["Cantidad_de_Cupones"].sum() else 0,
    }])

    return pd.concat([out, total_row], ignore_index=True)