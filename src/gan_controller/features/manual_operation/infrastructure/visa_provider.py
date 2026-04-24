import threading

import pyvisa

_RM_LOCK = threading.Lock()
_STATE: dict[str, pyvisa.ResourceManager | None] = {"shared_rm": None}


def _is_resource_manager_alive(resource_manager: pyvisa.ResourceManager) -> bool:
    try:
        resource_manager.list_resources()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[VISA][shared_rm] stale manager detected: {e}")
        return False


def _create_resource_manager() -> pyvisa.ResourceManager:
    resource_manager = pyvisa.ResourceManager()
    print("[VISA][shared_rm] created new resource manager")
    return resource_manager


def _dispose_resource_manager(resource_manager: pyvisa.ResourceManager) -> None:
    try:
        resource_manager.close()
        print("[VISA][shared_rm] disposed stale resource manager")
    except Exception as e:  # noqa: BLE001
        print(f"[VISA][shared_rm] failed to dispose stale manager: {e}")


def get_shared_resource_manager() -> pyvisa.ResourceManager:
    """manual_operation で共有する VISA ResourceManager を返す。"""
    with _RM_LOCK:
        resource_manager = _STATE["shared_rm"]
        if resource_manager is None:
            resource_manager = _create_resource_manager()
            _STATE["shared_rm"] = resource_manager
            return resource_manager

        if not _is_resource_manager_alive(resource_manager):
            _dispose_resource_manager(resource_manager)
            resource_manager = _create_resource_manager()
            _STATE["shared_rm"] = resource_manager

        return resource_manager
