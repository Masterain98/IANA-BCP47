"""Update the bundled IANA Language Subtag Registry and patch version."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
import urllib.request
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from iana_bcp47._registry import Registry, RegistryFormatError, parse_registry

REGISTRY_URL = "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry"
MINIMUM_COUNTS = {
    "language": 7000,
    "extlang": 200,
    "script": 150,
    "region": 250,
    "variant": 80,
    "grandfathered": 20,
}
VERSION_PATTERN = re.compile(r'(?m)^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$')
TABLE_PATTERN = re.compile(r"(?m)^\[[^]]+]\s*$")


@dataclass(frozen=True, slots=True)
class UpdateResult:
    changed: bool
    old_registry: Registry
    new_registry: Registry
    old_version: str
    new_version: str


def fetch_registry(
    url: str = REGISTRY_URL,
    timeout: float = 30,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> bytes:
    """Fetch a registry snapshot with an explicit timeout."""

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "iana-bcp47-updater/0.2 (+https://github.com/Masterain98/iana-bcp47)"
        },
    )
    with opener(request, timeout=timeout) as response:  # type: ignore[attr-defined]
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(f"IANA returned HTTP {status}.")
        return response.read()  # type: ignore[no-any-return]


def decode_registry(raw: bytes) -> tuple[str, Registry]:
    """Strictly decode and validate one downloaded snapshot."""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryFormatError("Registry is not valid UTF-8.") from exc
    registry = parse_registry(text)
    counts = Counter(entry.type for entry in registry.entries)
    missing = [
        f"{kind}={counts[kind]} (minimum {minimum})"
        for kind, minimum in MINIMUM_COUNTS.items()
        if counts[kind] < minimum
    ]
    if missing:
        raise RegistryFormatError("Registry failed count sanity checks: " + ", ".join(missing))
    for kind in ("language", "script", "region"):
        if not registry.ranges[kind]:
            raise RegistryFormatError(f"Registry has no {kind} range record.")
    return text, registry


def _project_version_match(pyproject_text: str) -> re.Match[str]:
    project = re.search(r"(?m)^\[project]\s*$", pyproject_text)
    if project is None:
        raise ValueError("Could not find a [project] table in pyproject.toml.")
    next_table = TABLE_PATTERN.search(pyproject_text, project.end())
    section_end = next_table.start() if next_table else len(pyproject_text)
    match = VERSION_PATTERN.search(pyproject_text, project.end(), section_end)
    if match is None:
        raise ValueError("Could not find a simple X.Y.Z version in the [project] table.")
    return match


def bump_patch_version(pyproject_text: str) -> tuple[str, str, str]:
    """Increment the PEP 621 project version by one patch."""

    match = _project_version_match(pyproject_text)
    major, minor, patch = (int(value) for value in match.groups())
    old_version = f"{major}.{minor}.{patch}"
    new_version = f"{major}.{minor}.{patch + 1}"
    updated = (
        pyproject_text[: match.start()]
        + f'version = "{new_version}"'
        + pyproject_text[match.end() :]
    )
    return updated, old_version, new_version


def _write_temp(target: Path, data: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _replace_pair(
    registry_path: Path, registry_data: bytes, project_path: Path, project_data: bytes
) -> None:
    """Replace both tracked files, rolling back the first if the second fails."""

    old_registry = registry_path.read_bytes()
    registry_temp = _write_temp(registry_path, registry_data)
    project_temp = _write_temp(project_path, project_data)
    try:
        os.replace(registry_temp, registry_path)
        try:
            os.replace(project_temp, project_path)
        except BaseException:
            rollback = _write_temp(registry_path, old_registry)
            os.replace(rollback, registry_path)
            raise
    finally:
        registry_temp.unlink(missing_ok=True)
        project_temp.unlink(missing_ok=True)


def update_registry(
    raw: bytes,
    registry_path: Path,
    pyproject_path: Path,
    *,
    dry_run: bool = False,
) -> UpdateResult:
    """Validate and, when changed, atomically update data and the patch version."""

    current_raw = registry_path.read_bytes()
    _, old_registry = decode_registry(current_raw)
    _, new_registry = decode_registry(raw)
    project_text = pyproject_path.read_text(encoding="utf-8")
    version_match = _project_version_match(project_text)
    old_version = ".".join(version_match.groups())

    if new_registry.file_date < old_registry.file_date:
        raise RegistryFormatError(
            f"Registry date regressed from {old_registry.file_date} to {new_registry.file_date}."
        )
    if raw == current_raw:
        return UpdateResult(False, old_registry, new_registry, old_version, old_version)

    updated_project, _, new_version = bump_patch_version(project_text)
    if not dry_run:
        _replace_pair(
            registry_path,
            raw,
            pyproject_path,
            updated_project.encode("utf-8"),
        )
    return UpdateResult(True, old_registry, new_registry, old_version, new_version)


def render_summary(result: UpdateResult) -> str:
    old_counts = Counter(entry.type for entry in result.old_registry.entries)
    new_counts = Counter(entry.type for entry in result.new_registry.entries)
    lines = [
        "Automated update of the bundled IANA Language Subtag Registry.",
        "",
        f"- Registry date: `{result.old_registry.file_date}` → `{result.new_registry.file_date}`",
        f"- Package version: `{result.old_version}` → `{result.new_version}`",
        "",
        "| Type | Before | After | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for kind in sorted(set(old_counts) | set(new_counts)):
        delta = new_counts[kind] - old_counts[kind]
        lines.append(f"| {kind} | {old_counts[kind]} | {new_counts[kind]} | {delta:+d} |")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=REGISTRY_URL)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("src/iana_bcp47/language-subtag-registry.txt"),
    )
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--summary-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = update_registry(
        fetch_registry(args.url, args.timeout),
        args.registry,
        args.pyproject,
        dry_run=args.dry_run,
    )
    summary = render_summary(result)
    print(summary, end="")
    if args.summary_file:
        args.summary_file.write_text(summary, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
