from __future__ import annotations

from importlib.metadata import version

import iana_bcp47
from iana_bcp47.bcp47 import (
    extlang_codes,
    grandfathered_codes,
    language_codes,
    redundant_codes,
    region_codes,
    script_codes,
    variant_codes,
)


def test_public_validator_and_version_are_exposed() -> None:
    assert callable(iana_bcp47.validate_bcp47)
    assert iana_bcp47.__version__ == version("iana-bcp47")


def test_legacy_dictionaries_remain_available() -> None:
    assert language_codes["en"] == "English"
    assert "cmn" in extlang_codes
    assert "Latn" in script_codes
    assert "US" in region_codes
    assert "1901" in variant_codes
    assert redundant_codes
    assert grandfathered_codes["i-klingon"]
    assert iana_bcp47.language_codes is language_codes
