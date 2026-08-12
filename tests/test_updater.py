from __future__ import annotations

import os
from pathlib import Path

import pytest

from iana_bcp47._registry import RegistryFormatError
from tools import update_registry as updater


def registry_snapshot(file_date: str, description: str = "Afar") -> bytes:
    return f"""File-Date: {file_date}
%%
Type: language
Subtag: aa
Description: {description}
Added: 2005-10-16
%%
Type: language
Subtag: qaa..qtz
Description: Reserved for local use
Added: 2005-10-16
%%
Type: extlang
Subtag: abc
Description: Example
Added: 2009-07-29
Prefix: aa
%%
Type: script
Subtag: Qaaa..Qabx
Description: Private use
Added: 2005-10-16
%%
Type: region
Subtag: QM..QZ
Description: Private use
Added: 2005-10-16
%%
Type: variant
Subtag: 1901
Description: Traditional orthography
Added: 2005-10-16
%%
Type: grandfathered
Tag: i-example
Description: Example
Added: 2005-10-16
""".encode()


@pytest.fixture(autouse=True)
def lower_count_thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(updater, "MINIMUM_COUNTS", {kind: 0 for kind in updater.MINIMUM_COUNTS})


def make_project(tmp_path: Path, registry: bytes | None = None) -> tuple[Path, Path]:
    registry_path = tmp_path / "language-subtag-registry.txt"
    project_path = tmp_path / "pyproject.toml"
    registry_path.write_bytes(registry or registry_snapshot("2026-01-01"))
    project_path.write_text('[project]\nversion = "0.2.0"\n', encoding="utf-8")
    return registry_path, project_path


def test_unchanged_registry_does_not_bump_version(tmp_path: Path) -> None:
    registry_path, project_path = make_project(tmp_path)
    result = updater.update_registry(registry_path.read_bytes(), registry_path, project_path)
    assert not result.changed
    assert result.new_version == "0.2.0"
    assert 'version = "0.2.0"' in project_path.read_text(encoding="utf-8")


def test_changed_registry_updates_data_and_patch_version(tmp_path: Path) -> None:
    registry_path, project_path = make_project(tmp_path)
    new_data = registry_snapshot("2026-02-01", "Updated")
    result = updater.update_registry(new_data, registry_path, project_path)
    assert result.changed
    assert result.new_version == "0.2.1"
    assert registry_path.read_bytes() == new_data
    assert 'version = "0.2.1"' in project_path.read_text(encoding="utf-8")
    assert "| language |" in updater.render_summary(result)


def test_patch_bump_only_changes_the_project_table() -> None:
    text = '[tool.example]\nversion = "9.9.9"\n\n[project]\nversion = "0.2.0"\n'
    updated, old_version, new_version = updater.bump_patch_version(text)
    assert old_version == "0.2.0"
    assert new_version == "0.2.1"
    assert 'version = "9.9.9"' in updated
    assert '[project]\nversion = "0.2.1"' in updated


def test_dry_run_changes_nothing(tmp_path: Path) -> None:
    registry_path, project_path = make_project(tmp_path)
    old_project = project_path.read_bytes()
    result = updater.update_registry(
        registry_snapshot("2026-02-01"), registry_path, project_path, dry_run=True
    )
    assert result.changed
    assert registry_path.read_bytes() == registry_snapshot("2026-01-01")
    assert project_path.read_bytes() == old_project


def test_registry_date_cannot_regress(tmp_path: Path) -> None:
    registry_path, project_path = make_project(tmp_path)
    with pytest.raises(RegistryFormatError, match="regressed"):
        updater.update_registry(registry_snapshot("2025-12-31"), registry_path, project_path)


def test_invalid_utf8_and_truncated_registry_are_rejected() -> None:
    with pytest.raises(RegistryFormatError, match="UTF-8"):
        updater.decode_registry(b"\xff")
    with pytest.raises(RegistryFormatError):
        updater.decode_registry(b"File-Date: 2026-01-01\n%%\n")


def test_registry_count_sanity_checks_reject_partial_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(updater, "MINIMUM_COUNTS", {"language": 3})
    with pytest.raises(RegistryFormatError, match="count sanity checks"):
        updater.decode_registry(registry_snapshot("2026-01-01"))


class FakeResponse:
    def __init__(self, data: bytes, status: int = 200) -> None:
        self.data = data
        self.status = status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.data


def test_fetch_registry_uses_timeout_and_checks_status() -> None:
    captured: dict[str, object] = {}

    def opener(request: object, *, timeout: float) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(b"data")

    assert updater.fetch_registry(timeout=4, opener=opener) == b"data"
    assert captured["timeout"] == 4

    with pytest.raises(RuntimeError, match="HTTP 503"):
        updater.fetch_registry(opener=lambda *args, **kwargs: FakeResponse(b"", 503))


def test_fetch_registry_propagates_timeout() -> None:
    def timeout(*args: object, **kwargs: object) -> FakeResponse:
        raise TimeoutError("timed out")

    with pytest.raises(TimeoutError):
        updater.fetch_registry(opener=timeout)


def test_pair_replacement_rolls_back_first_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry_path, project_path = make_project(tmp_path)
    old_registry = registry_path.read_bytes()
    old_project = project_path.read_bytes()
    real_replace = os.replace
    calls = 0

    def fail_second(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated project replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr(updater.os, "replace", fail_second)
    with pytest.raises(OSError, match="simulated"):
        updater._replace_pair(registry_path, b"new registry", project_path, b"new project")
    assert registry_path.read_bytes() == old_registry
    assert project_path.read_bytes() == old_project


def test_pair_replacement_cleans_registry_temp_when_project_staging_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry_path, project_path = make_project(tmp_path)
    real_write_temp = updater._write_temp
    registry_temp: Path | None = None
    calls = 0

    def fail_project_staging(target: Path, data: bytes) -> Path:
        nonlocal calls, registry_temp
        calls += 1
        if calls == 2:
            raise OSError("simulated project staging failure")
        registry_temp = real_write_temp(target, data)
        return registry_temp

    monkeypatch.setattr(updater, "_write_temp", fail_project_staging)
    with pytest.raises(OSError, match="staging failure"):
        updater._replace_pair(registry_path, b"new registry", project_path, b"new project")
    assert registry_temp is not None
    assert not registry_temp.exists()
