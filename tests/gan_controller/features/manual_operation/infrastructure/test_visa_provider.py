import pytest

from gan_controller.features.manual_operation.infrastructure import visa_provider


class _StubResourceManager:
    def __init__(self, *, alive: bool = True) -> None:
        self.alive = alive
        self.closed = False

    def list_resources(self) -> tuple[str, ...]:
        if not self.alive:
            msg = "Invalid session handle. The resource might be closed."
            raise RuntimeError(msg)
        return ()

    def close(self) -> None:
        self.closed = True


def test_get_shared_resource_manager_returns_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def _factory() -> _StubResourceManager:
        nonlocal calls
        calls += 1
        return _StubResourceManager(alive=True)

    monkeypatch.setattr(visa_provider, "_STATE", {"shared_rm": None})
    monkeypatch.setattr(visa_provider.pyvisa, "ResourceManager", _factory)

    rm1 = visa_provider.get_shared_resource_manager()
    rm2 = visa_provider.get_shared_resource_manager()

    assert rm1 is rm2
    assert calls == 1


def test_get_shared_resource_manager_recreates_stale_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_manager = _StubResourceManager(alive=False)
    calls = 0

    def _factory() -> _StubResourceManager:
        nonlocal calls
        calls += 1
        return _StubResourceManager(alive=True)

    monkeypatch.setattr(visa_provider, "_STATE", {"shared_rm": stale_manager})
    monkeypatch.setattr(visa_provider.pyvisa, "ResourceManager", _factory)

    recovered_manager = visa_provider.get_shared_resource_manager()

    assert recovered_manager is not stale_manager
    assert stale_manager.closed is True
    assert visa_provider._STATE["shared_rm"] is recovered_manager  # noqa: SLF001
    assert calls == 1
