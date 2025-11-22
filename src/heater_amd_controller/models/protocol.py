from dataclasses import asdict, dataclass, field

from heater_amd_controller.models.sequence import SequenceMode


@dataclass
class ProtocolConfig:
    name: str

    # --- シーケンス時間設定 ---
    sequence_hours: dict[str, float] = field(default_factory=dict)

    # --- HC電流 ---
    hc_enabled: bool = True
    hc_current: float = 3.0

    # --- AMD電流 ---
    amd_enabled: bool = True
    amd_current: float = 3.0

    # --- その他設定 ---
    repeat_count: int = 1
    step_interval: int = 10

    def to_dict(self) -> dict:
        """TOML保存用に辞書化する"""
        return asdict(self)

    @classmethod
    def default(cls) -> "ProtocolConfig":
        """新規作成用のデフォルト設定"""
        return cls(
            name="新しいプロトコル...",
            sequence_hours={
                SequenceMode.RISING.value: 1.0,
                SequenceMode.HEAT_CLEANING.value: 1.0,
                SequenceMode.DECREASE.value: 0.5,
                SequenceMode.WAIT.value: 7.5,
            },
            repeat_count=1,
            step_interval=10,
            hc_enabled=True,
            hc_current=3.0,
            amd_enabled=True,
            amd_current=3.0,
        )
