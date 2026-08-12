"""Parser and cached access to the IANA Language Subtag Registry."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from functools import cached_property, lru_cache
from importlib.resources import files
from types import MappingProxyType

KNOWN_TYPES = frozenset(
    {"language", "extlang", "script", "region", "variant", "grandfathered", "redundant"}
)


class RegistryFormatError(ValueError):
    """Raised when a registry snapshot is malformed."""


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """One record from the IANA registry."""

    type: str
    identifier: str
    fields: Mapping[str, tuple[str, ...]] = field(hash=False)

    @property
    def descriptions(self) -> tuple[str, ...]:
        return self.fields.get("Description", ())

    @property
    def deprecated(self) -> str | None:
        values = self.fields.get("Deprecated", ())
        return values[0] if values else None

    @property
    def preferred_value(self) -> str | None:
        values = self.fields.get("Preferred-Value", ())
        return values[0] if values else None

    @property
    def prefixes(self) -> tuple[str, ...]:
        return self.fields.get("Prefix", ())

    @property
    def suppress_script(self) -> str | None:
        values = self.fields.get("Suppress-Script", ())
        return values[0] if values else None

    def description(self) -> str:
        text = "; ".join(self.descriptions) or self.identifier
        if self.deprecated:
            text += f" (deprecated {self.deprecated}"
            if self.preferred_value:
                text += f"; prefer {self.preferred_value}"
            text += ")"
        return text


@dataclass(frozen=True)
class Registry:
    """A parsed IANA registry snapshot with case-insensitive indexes."""

    file_date: date
    entries: tuple[RegistryEntry, ...]

    @cached_property
    def by_type(self) -> Mapping[str, Mapping[str, RegistryEntry]]:
        indexes: dict[str, dict[str, RegistryEntry]] = {kind: {} for kind in KNOWN_TYPES}
        for entry in self.entries:
            key = entry.identifier.casefold()
            if key in indexes[entry.type]:
                raise RegistryFormatError(
                    f"Duplicate {entry.type} identifier {entry.identifier!r} in registry."
                )
            indexes[entry.type][key] = entry
        return MappingProxyType(
            {kind: MappingProxyType(entries) for kind, entries in indexes.items()}
        )

    @cached_property
    def ranges(self) -> Mapping[str, tuple[tuple[str, str, RegistryEntry], ...]]:
        ranges: dict[str, list[tuple[str, str, RegistryEntry]]] = {kind: [] for kind in KNOWN_TYPES}
        for entry in self.entries:
            if ".." not in entry.identifier:
                continue
            start, end = entry.identifier.casefold().split("..", 1)
            ranges[entry.type].append((start, end, entry))
        return MappingProxyType({kind: tuple(values) for kind, values in ranges.items()})

    def lookup(self, kind: str, identifier: str) -> RegistryEntry | None:
        """Look up an exact identifier or an IANA private-use range."""

        normalized = identifier.casefold()
        exact = self.by_type.get(kind, {}).get(normalized)
        if exact is not None:
            return exact
        for start, end, entry in self.ranges.get(kind, ()):
            if len(start) == len(normalized) == len(end) and start <= normalized <= end:
                return entry
        return None

    def entries_of_type(self, kind: str) -> Iterable[RegistryEntry]:
        return (entry for entry in self.entries if entry.type == kind)


def _finish_record(fields: dict[str, list[str]]) -> RegistryEntry:
    kind_values = fields.get("Type", [])
    if len(kind_values) != 1 or kind_values[0] not in KNOWN_TYPES:
        raise RegistryFormatError("Each registry record must contain one known Type field.")
    kind = kind_values[0]
    identifier_field = "Tag" if kind in {"grandfathered", "redundant"} else "Subtag"
    identifiers = fields.get(identifier_field, [])
    if len(identifiers) != 1:
        raise RegistryFormatError(f"{kind} records must contain one {identifier_field} field.")
    if not fields.get("Description"):
        raise RegistryFormatError(f"Registry record {identifiers[0]!r} has no Description.")
    immutable_fields = MappingProxyType({key: tuple(values) for key, values in fields.items()})
    return RegistryEntry(kind, identifiers[0], immutable_fields)


def parse_registry(text: str) -> Registry:
    """Parse a complete registry snapshot without discarding metadata."""

    if not isinstance(text, str):
        raise TypeError("Registry text must be a string.")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("File-Date: "):
        raise RegistryFormatError("Registry must begin with a File-Date header.")
    try:
        file_date = date.fromisoformat(lines[0].split(": ", 1)[1])
    except ValueError as exc:
        raise RegistryFormatError("Registry File-Date is not a valid ISO date.") from exc

    entries: list[RegistryEntry] = []
    fields: dict[str, list[str]] = {}
    last_key: str | None = None
    saw_separator = False
    for line in lines[1:]:
        if line == "%%":
            saw_separator = True
            if fields:
                entries.append(_finish_record(fields))
                fields = {}
            last_key = None
            continue
        if not line:
            continue
        if ": " in line and not line[0].isspace():
            key, value = line.split(": ", 1)
            if not key or not value:
                raise RegistryFormatError("Registry fields cannot be empty.")
            fields.setdefault(key, []).append(value)
            last_key = key
            continue
        if line[0].isspace() and last_key is not None:
            fields[last_key][-1] += f" {line.strip()}"
            continue
        raise RegistryFormatError(f"Malformed registry line: {line!r}")

    if fields:
        entries.append(_finish_record(fields))
    if not saw_separator or not entries:
        raise RegistryFormatError("Registry contains no records.")
    registry = Registry(file_date=file_date, entries=tuple(entries))
    _ = registry.by_type  # Force duplicate detection while parsing.
    return registry


@lru_cache(maxsize=1)
def get_registry() -> Registry:
    """Load and cache the registry bundled with the installed package."""

    registry_file = files("iana_bcp47").joinpath("language-subtag-registry.txt")
    return parse_registry(registry_file.read_text(encoding="utf-8"))
