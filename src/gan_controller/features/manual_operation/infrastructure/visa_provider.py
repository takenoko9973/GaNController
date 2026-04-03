import threading

import pyvisa

_RM_LOCK = threading.Lock()
_STATE: dict[str, pyvisa.ResourceManager | None] = {"shared_rm": None}


def get_shared_resource_manager() -> pyvisa.ResourceManager:
    """manual_operation で共有する VISA ResourceManager を返す。"""
    with _RM_LOCK:
        resource_manager = _STATE["shared_rm"]
        if resource_manager is None:
            resource_manager = pyvisa.ResourceManager()
            _STATE["shared_rm"] = resource_manager
        return resource_manager
