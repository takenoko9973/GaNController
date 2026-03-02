import importlib
import os
from pathlib import Path
from types import ModuleType

import pytest

MODULE_NAME = "gan_controller.core.constants"


def _reload_constants() -> ModuleType:
    module = importlib.import_module(MODULE_NAME)
    return importlib.reload(module)


@pytest.fixture(autouse=True)
def _restore_constants_module():  # noqa: ANN202
    # 各テストで環境変数やcwdを書き換えるため、終了時に定数モジュールを再評価する。
    yield
    _reload_constants()


def test_env_var_home_has_highest_priority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    custom_home = tmp_path / "custom-home"

    monkeypatch.setenv("GAN_CONTROLLER_HOME", str(custom_home))
    module = _reload_constants()

    assert custom_home.resolve(strict=False) == module.APP_HOME


def test_project_root_is_detected_from_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    nested = repo_root / "nested" / "work"
    nested.mkdir(parents=True)
    (repo_root / "pyproject.toml").write_text("[project]\nname = 'dummy'\n", encoding="utf-8")

    monkeypatch.delenv("GAN_CONTROLLER_HOME", raising=False)
    monkeypatch.chdir(nested)
    module = _reload_constants()

    assert repo_root.resolve(strict=False) == module.APP_HOME


def test_os_data_dir_fallback_when_no_env_or_pyproject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    monkeypatch.delenv("GAN_CONTROLLER_HOME", raising=False)
    monkeypatch.chdir(work_dir)

    data_home = tmp_path / "data-home"
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", str(data_home))
    else:
        monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    module = _reload_constants()

    expected_home = (data_home / "GaNController").resolve(strict=False)
    assert expected_home == module.APP_HOME


def test_ensure_runtime_dirs_creates_required_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app_home = tmp_path / "app-home"

    monkeypatch.setenv("GAN_CONTROLLER_HOME", str(app_home))
    module = _reload_constants()
    module.ensure_runtime_dirs()

    assert module.CONFIG_DIR.is_dir()
    assert module.LOG_DIR.is_dir()
    assert module.PROTOCOLS_DIR.is_dir()
