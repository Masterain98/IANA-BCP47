"""IANA-backed RFC 5646 language-tag validation."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .validator import validate_bcp47

try:
    __version__ = version("iana-bcp47")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0+unknown"

_DICTIONARY_EXPORTS = {
    "extlang_codes",
    "grandfathered_codes",
    "language_codes",
    "redundant_codes",
    "region_codes",
    "script_codes",
    "variant_codes",
}


def __getattr__(name: str) -> Any:
    if name in _DICTIONARY_EXPORTS:
        from . import bcp47

        return getattr(bcp47, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["__version__", "validate_bcp47", *_DICTIONARY_EXPORTS]
