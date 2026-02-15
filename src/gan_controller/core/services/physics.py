from gan_controller.core.constants import (
    ELEMENTARY_CHARGE,
    PLANCK_CONSTANT,
    SPEED_OF_LIGHT,
)


def calculate_quantum_efficiency(
    current_amp: float, laser_power_watt: float, wavelength_nm: float
) -> float:
    """
    量子効率 (QE) を計算する。

    Formula:
        QE[%] = (Electrons / Photons) * 100
              = (I / e) / (P / E_photon) * 100
              = (I / e) / (P / (hc / lambda)) * 100
              = (I * h * c) / (e * P * lambda) * 100

    Args:
        current_amp (float): 光電流 [A]
        laser_power_watt (float): レーザーパワー [W]
        wavelength_nm (float): 波長 [nm]

    Returns:
        float: 量子効率 [%]

    """
    # ゼロ除算防止
    if laser_power_watt == 0 or wavelength_nm == 0:
        return 0.0

    # 波長を nm -> m に変換
    wavelength_m = wavelength_nm * 1e-9

    # 分子: I * h * c
    numerator = current_amp * PLANCK_CONSTANT * SPEED_OF_LIGHT

    # 分母: e * P * lambda
    denominator = ELEMENTARY_CHARGE * laser_power_watt * wavelength_m

    # 結果計算
    return (numerator / denominator) * 100.0
