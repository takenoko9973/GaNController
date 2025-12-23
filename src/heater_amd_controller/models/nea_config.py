from dataclasses import dataclass


@dataclass
class NEAConfig:
    # --- レーザー設定 ---
    laser_setpoint: float = 0.0  # 設定値 (V or mW) - Applyボタンで反映
    laser_power_energy: float = 164e-6  # 計算用エネルギー値 (W)

    # --- 計測設定 ---
    resistance: float = 1.0e6  # 換算抵抗 (Ω)
    hv_value: float = 100.0  # HV値 (V)

    # --- ログ設定 ---
    log_date_update: bool = False
    log_major_update: bool = False
    comment: str = ""

    # --- 実行設定 ---
    interval_sec: float = 1.0
