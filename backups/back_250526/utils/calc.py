def ext_calculation_pressure(value: float) -> float:
    return 10 ** (value - 10)


def sip_calculation_pressure(value: float) -> float:
    # V = 2(log(Pa) - log(Pa(0))) Pa(0)はSIPの種類による (マニュアル参照)
    p0 = 5 * 10 ** (-7)
    return p0 * 10 ** (value / 2)
