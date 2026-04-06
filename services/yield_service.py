import pandas as pd

from reports import build_yield_by_route


def prepare_yield_by_route_outputs(coupons_long: pd.DataFrame):
    yield_by_route_df = build_yield_by_route(coupons_long)

    return {
        "yield_by_route_df": yield_by_route_df,
    }