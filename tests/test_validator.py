from __future__ import annotations

import pytest

from iana_bcp47 import validate_bcp47


@pytest.mark.parametrize(
    "tag",
    [
        "en",
        "en-US",
        "EN-us",
        "zh-Hant-CN",
        "de-CH-1901",
        "i-klingon",
        "en-u-ca-gregory",
        "en-x-private",
        "x-private",
        "qaa",
        "en-QM",
        "en-Qaaa",
        "iw",
        "en-BU",
    ],
)
def test_valid_rfc5646_tags(tag: str) -> None:
    valid, description = validate_bcp47(tag)
    assert valid, description
    assert description


@pytest.mark.parametrize(
    ("tag", "message_fragment"),
    [
        ("", "empty"),
        ("-en", "empty subtags"),
        ("en-", "empty subtags"),
        ("en--US", "empty subtags"),
        ("en-US-Latn", "invalid position"),
        ("en-US-US", "invalid position"),
        ("sl-rozaj-rozaj", "repeated"),
        ("en-a-abc-a-def", "repeated"),
        ("en-a", "no payload"),
        ("zzzzzzzz", "not a registered language"),
        ("en-1234", "not a registered variant"),
        ("en-💥", "ASCII"),
    ],
)
def test_invalid_tags(tag: str, message_fragment: str) -> None:
    valid, message = validate_bcp47(tag)
    assert not valid
    assert message_fragment.casefold() in message.casefold()


def test_prefix_is_metadata_not_a_validity_gate() -> None:
    valid, message = validate_bcp47("en-cmn")
    assert valid, message


def test_deprecated_tag_includes_replacement_guidance() -> None:
    valid, message = validate_bcp47("iw")
    assert valid
    assert "deprecated" in message
    assert "prefer he" in message


def test_non_string_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="string"):
        validate_bcp47(None)  # type: ignore[arg-type]
