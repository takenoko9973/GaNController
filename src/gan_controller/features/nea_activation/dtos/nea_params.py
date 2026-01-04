from dataclasses import dataclass

from gan_controller.common.types.quantity import Quantity


@dataclass(frozen=True)
class NEAConditionParams:
    """実験中不変の設定値"""

    shunt_resistance: Quantity  # 換算抵抗 (シャント抵抗)
    laser_wavelength: Quantity  # レーザー波長
    stabilization_time: Quantity  # 安定化時間
    integration_count: Quantity  # 積算間隔
    integration_interval: Quantity  # 積算間隔


@dataclass
class NEALogParams:
    """ログ設定パラメータ

    UIからRunnerへ渡される一時的な設定
    """

    update_date_folder: bool
    update_major_version: bool
    comment: str


@dataclass
class NEAControlParams:
    """実行制御パラメータ (Runtime State)

    実験中のデバイス制御値や状態を保持する
    """

    amd_enable: bool  # AMDを有効化するか
    amd_output_current: Quantity  # AMD出力電流
    laser_power_sv: Quantity  # レーザー出力電力 (SV)
    laser_power_output: Quantity  # レーザー出力電力 (実出力)
