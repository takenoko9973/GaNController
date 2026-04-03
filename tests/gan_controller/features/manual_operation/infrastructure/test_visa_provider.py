import pytest

from gan_controller.features.manual_operation.infrastructure import visa_provider


class _StubResourceManager:
    pass


def test_get_shared_resource_manager_returns_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def _factory() -> _StubResourceManager:
        nonlocal calls
        calls += 1
        return _StubResourceManager()

    monkeypatch.setattr(visa_provider, "_STATE", {"shared_rm": None})
    monkeypatch.setattr(visa_provider.pyvisa, "ResourceManager", _factory)

    rm1 = visa_provider.get_shared_resource_manager()
    rm2 = visa_provider.get_shared_resource_manager()

    assert rm1 is rm2
    assert calls == 1
