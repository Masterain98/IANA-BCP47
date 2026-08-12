"""Backward-compatible dictionaries generated from the bundled registry."""

from __future__ import annotations

from ._registry import get_registry


def _descriptions(kind: str) -> dict[str, str]:
    return {entry.identifier: entry.description() for entry in get_registry().entries_of_type(kind)}


language_codes = _descriptions("language")
extlang_codes = _descriptions("extlang")
script_codes = _descriptions("script")
region_codes = _descriptions("region")
variant_codes = _descriptions("variant")
redundant_codes = _descriptions("redundant")
grandfathered_codes = _descriptions("grandfathered")

__all__ = [
    "extlang_codes",
    "grandfathered_codes",
    "language_codes",
    "redundant_codes",
    "region_codes",
    "script_codes",
    "variant_codes",
]
