import math

import pandas as pd


def format_number_es(value, decimals=2, blank_for_null=True):
    if value is None:
        return "" if blank_for_null else f"{0:.{decimals}f}".replace(".", ",")

    try:
        if pd.isna(value):
            return "" if blank_for_null else f"{0:.{decimals}f}".replace(".", ",")
    except Exception:
        pass

    try:
        number = float(value)
    except Exception:
        try:
            number = float(str(value).strip())
        except Exception:
            return str(value)

    if math.isnan(number) or math.isinf(number):
        return "" if blank_for_null else f"{0:.{decimals}f}".replace(".", ",")

    fmt = f"{{:,.{decimals}f}}".format(number)
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def format_int_es(value, blank_for_null=True):
    if value is None:
        return "" if blank_for_null else "0"

    try:
        if pd.isna(value):
            return "" if blank_for_null else "0"
    except Exception:
        pass

    try:
        number = int(round(float(value)))
    except Exception:
        return str(value)

    return f"{number:,}".replace(",", ".")


def format_money_es(value, decimals=2, currency_symbol=""):
    formatted = format_number_es(value, decimals=decimals, blank_for_null=True)
    if formatted == "":
        return ""
    return f"{currency_symbol}{formatted}" if currency_symbol else formatted


def metric_text_number(value, decimals=2):
    return format_number_es(value, decimals=decimals, blank_for_null=False)


def metric_text_int(value):
    return format_int_es(value, blank_for_null=False)


def metric_text_money(value, decimals=2):
    return format_money_es(value, decimals=decimals)