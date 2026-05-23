def vnd(value):
    return f"{value:,.0f}".replace(",", ".")

CNY_RATE = 3875

def cny(vnd_value):
    cny_value = vnd_value / CNY_RATE
    return f"CNY {cny_value:,.0f}".replace(",", ".")

def vnd_decimal(value):
    s = f"{value:,.2f}"

    # 20,729,255.92
    # -> 20.729.255,92

    return s.replace(",", "_").replace(".", ",").replace("_", ".")