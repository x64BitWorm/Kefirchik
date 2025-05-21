def formatMoney(value: float) -> str:
    rounded_value = round(value, 2)
    return str(int(rounded_value)) if rounded_value.is_integer() else str(rounded_value)
