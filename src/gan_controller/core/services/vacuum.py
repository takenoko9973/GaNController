def calc_ext_pressure_from_voltage(voltage_v: float) -> float:
    """
    EXT真空計の電圧(V)から圧力(Pa)を計算する

    式: P = 10^(V - 10)
    """
    return 10 ** (voltage_v - 10)


def calc_sip_pressure_from_voltage(voltage_v: float, p0: float = 5e-7) -> float:
    """
    SIP真空計の電圧(V)から圧力(Pa)を計算する

    式: V = 2 * (log10(P) - log10(P0))  => P = P0 * 10^(V/2)
    Pa(0)はSIPの種類による (マニュアル参照)
    """
    return p0 * (10 ** (voltage_v / 2))
