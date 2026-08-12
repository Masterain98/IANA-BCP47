"""RFC 5646 language-tag validation."""

from __future__ import annotations

from ._registry import Registry, RegistryEntry, get_registry


def _is_alpha(value: str, minimum: int, maximum: int) -> bool:
    return minimum <= len(value) <= maximum and value.isascii() and value.isalpha()


def _is_alnum(value: str, minimum: int, maximum: int) -> bool:
    return minimum <= len(value) <= maximum and value.isascii() and value.isalnum()


def _is_variant(value: str) -> bool:
    return _is_alnum(value, 5, 8) or (
        len(value) == 4 and value[0].isascii() and value[0].isdigit() and value[1:].isalnum()
    )


def _entry_description(entry: RegistryEntry) -> str:
    return entry.description()


def _lookup(
    registry: Registry,
    kind: str,
    subtag: str,
    descriptions: list[str],
) -> str | None:
    entry = registry.lookup(kind, subtag)
    if entry is None:
        return f"{subtag} is not a registered {kind} subtag."
    descriptions.append(_entry_description(entry))
    return None


def _validate_private_use(parts: list[str], start: int) -> tuple[bool, str]:
    values = parts[start + 1 :]
    if not values or any(not _is_alnum(value, 1, 8) for value in values):
        return False, "Private-use section must contain 1-8 character alphanumeric subtags."
    return True, f"private use: {'-'.join(values)}"


def validate_bcp47(tag: str) -> tuple[bool, str]:
    """Validate *tag* against RFC 5646 and the bundled IANA registry.

    Registered deprecated and private-use-range subtags remain valid. Extension
    payloads are validated syntactically; extension-specific semantics are out
    of scope.
    """

    if not isinstance(tag, str):
        raise TypeError("tag must be a string")
    if not tag:
        return False, "Language tag cannot be empty."
    if not tag.isascii():
        return False, "Language tags must contain ASCII characters only."
    if tag.startswith("-") or tag.endswith("-") or "--" in tag:
        return False, "Language tags cannot contain empty subtags."

    parts = tag.split("-")
    registry = get_registry()
    normalized = tag.casefold()

    special = registry.lookup("grandfathered", normalized)
    if special is not None:
        return True, _entry_description(special)
    redundant = registry.lookup("redundant", normalized)
    if redundant is not None:
        return True, _entry_description(redundant)

    if parts[0].casefold() == "x":
        return _validate_private_use(parts, 0)

    primary = parts[0]
    if not (_is_alpha(primary, 2, 3) or _is_alpha(primary, 4, 4) or _is_alpha(primary, 5, 8)):
        return False, f"{primary} is not a well-formed primary language subtag."

    descriptions: list[str] = []
    error = _lookup(registry, "language", primary, descriptions)
    if error:
        return False, error

    index = 1
    if len(primary) in {2, 3}:
        extlang_count = 0
        while index < len(parts) and _is_alpha(parts[index], 3, 3) and extlang_count < 3:
            error = _lookup(registry, "extlang", parts[index], descriptions)
            if error:
                return False, error
            index += 1
            extlang_count += 1

    if index < len(parts) and _is_alpha(parts[index], 4, 4):
        error = _lookup(registry, "script", parts[index], descriptions)
        if error:
            return False, error
        index += 1

    if index < len(parts) and (
        _is_alpha(parts[index], 2, 2)
        or (len(parts[index]) == 3 and parts[index].isascii() and parts[index].isdigit())
    ):
        error = _lookup(registry, "region", parts[index], descriptions)
        if error:
            return False, error
        index += 1

    seen_variants: set[str] = set()
    while index < len(parts) and _is_variant(parts[index]):
        normalized_variant = parts[index].casefold()
        if normalized_variant in seen_variants:
            return False, f"Variant {parts[index]} is repeated."
        seen_variants.add(normalized_variant)
        error = _lookup(registry, "variant", parts[index], descriptions)
        if error:
            return False, error
        index += 1

    seen_singletons: set[str] = set()
    while index < len(parts) and len(parts[index]) == 1 and parts[index].casefold() != "x":
        singleton = parts[index]
        if not _is_alnum(singleton, 1, 1):
            return False, f"{singleton} is not a valid extension singleton."
        normalized_singleton = singleton.casefold()
        if normalized_singleton in seen_singletons:
            return False, f"Extension singleton {singleton} is repeated."
        seen_singletons.add(normalized_singleton)
        index += 1
        extension_start = index
        while index < len(parts) and _is_alnum(parts[index], 2, 8):
            index += 1
        if index == extension_start:
            return False, f"Extension {singleton} has no payload."
        descriptions.append(
            f"extension {singleton.casefold()}: {'-'.join(parts[extension_start:index])}"
        )

    if index < len(parts) and parts[index].casefold() == "x":
        valid, description = _validate_private_use(parts, index)
        if not valid:
            return False, description
        descriptions.append(description)
        index = len(parts)

    if index != len(parts):
        return False, f"{parts[index]} appears in an invalid position or is not well-formed."
    return True, " - ".join(descriptions)


__all__ = ["validate_bcp47"]
