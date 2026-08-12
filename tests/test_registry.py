from __future__ import annotations

import pytest

from iana_bcp47._registry import RegistryFormatError, get_registry, parse_registry

SAMPLE = """File-Date: 2026-08-08
%%
Type: language
Subtag: aa
Description: First description
Description: Second description
Added: 2005-10-16
Comments: first line
  continued line
Unknown-Field: retained
%%
Type: language
Subtag: qaa..qtz
Description: Reserved for local use
Added: 2005-10-16
%%
Type: extlang
Subtag: abc
Description: Example extlang
Added: 2009-07-29
Preferred-Value: abc
Prefix: zz
Prefix: yy
%%
Type: script
Subtag: Qaaa..Qabx
Description: Reserved for private use
Added: 2005-10-16
%%
Type: region
Subtag: QM..QZ
Description: Private use
Added: 2005-10-16
%%
Type: variant
Subtag: 1901
Description: Traditional German orthography
Added: 2005-10-16
%%
Type: grandfathered
Tag: i-example
Description: Example legacy tag
Added: 2001-01-01
Deprecated: 2002-01-01
Preferred-Value: aa
%%
Type: redundant
Tag: aa-Latn
Description: Example redundant tag
Added: 2001-01-01
"""


def test_parse_registry_preserves_metadata_and_repeated_fields() -> None:
    registry = parse_registry(SAMPLE)
    entry = registry.lookup("language", "AA")
    assert entry is not None
    assert entry.descriptions == ("First description", "Second description")
    assert entry.fields["Comments"] == ("first line continued line",)
    assert entry.fields["Unknown-Field"] == ("retained",)

    extlang = registry.lookup("extlang", "ABC")
    assert extlang is not None
    assert extlang.prefixes == ("zz", "yy")


def test_registry_range_lookups_are_case_insensitive() -> None:
    registry = parse_registry(SAMPLE)
    assert registry.lookup("language", "QAZ") is not None
    assert registry.lookup("script", "QAAZ") is not None
    assert registry.lookup("region", "qm") is not None
    assert registry.lookup("region", "US") is None


def test_packaged_registry_contains_required_record_types() -> None:
    registry = get_registry()
    assert registry.lookup("language", "en") is not None
    assert registry.lookup("grandfathered", "i-klingon") is not None
    assert registry.lookup("region", "QM") is not None


def test_entries_and_registries_are_hashable_without_ignoring_equality() -> None:
    registry = parse_registry(SAMPLE)
    entry = registry.lookup("language", "aa")
    assert entry is not None
    assert isinstance(hash(entry), int)
    assert isinstance(hash(registry), int)
    changed_fields = dict(entry.fields)
    changed_fields["Description"] = ("Different",)
    changed_entry = type(entry)(entry.type, entry.identifier, changed_fields)
    assert changed_entry != entry
    assert hash(changed_entry) == hash(entry)


def test_duplicate_casefolded_identifier_is_rejected() -> None:
    duplicate = (
        SAMPLE
        + """%%
Type: language
Subtag: AA
Description: Duplicate
Added: 2026-08-08
"""
    )
    with pytest.raises(RegistryFormatError, match="Duplicate language identifier"):
        parse_registry(duplicate)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "File-Date: not-a-date\n%%\n",
        "File-Date: 2026-01-01\nType: language\nSubtag: aa\nDescription: A\n",
        "File-Date: 2026-01-01\n%%\nType: language\nSubtag: aa\n",
        "File-Date: 2026-01-01\n%%\nnot a field\n",
    ],
)
def test_malformed_registry_is_rejected(text: str) -> None:
    with pytest.raises(RegistryFormatError):
        parse_registry(text)
