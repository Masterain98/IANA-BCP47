# IANA-BCP47

`iana-bcp47` validates language tags using the grammar from
[RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html) and the bundled
[IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry).
Validation is local and does not require a network connection.

## Features

- Case-insensitive RFC 5646 syntax and ordering validation.
- Registered language, extlang, script, region, and variant subtags.
- Grandfathered and redundant tags.
- Extensions and private-use tags, including IANA private-use ranges.
- Deprecated subtags remain valid and include replacement guidance when IANA provides it.
- Python 3.11 through 3.14.

Extension payloads are checked against the generic RFC 5646 grammar. This package does not
interpret extension-specific standards such as Unicode locale extension semantics. Registry
`Prefix` values are retained as metadata and guidance; RFC 5646 does not make them a validity
requirement.

## Installation

```console
pip install iana-bcp47
```

## Usage

```python
from iana_bcp47 import validate_bcp47

for tag in ["en-US", "EN-us", "zh-Hant-CN", "i-klingon", "x-private"]:
    valid, message = validate_bcp47(tag)
    print(tag, valid, message)
```

`validate_bcp47(tag)` returns `(valid, message)`. Invalid input returns `False` and an error
message; passing a non-string raises `TypeError`. The wording of descriptions and errors may
evolve as the IANA registry changes.

The legacy dictionaries remain available from `iana_bcp47.bcp47` and from the package root:

```python
from iana_bcp47 import language_codes, region_codes
```

## Data maintenance

The packaged registry date can be read from `iana_bcp47._registry.get_registry().file_date`.
A scheduled GitHub Actions workflow checks IANA every Monday. When the snapshot changes, it
updates the data, increments the package patch version, runs validation, and opens or refreshes
an `automation/iana-registry` pull request. A maintainer reviews and merges that PR; a successful
`main` CI run then publishes the new version through PyPI Trusted Publishing.

To inspect an update locally without modifying files:

```console
python -m pip install -e ".[dev]"
python tools/update_registry.py --dry-run
```

Run the maintenance checks with:

```console
ruff check .
ruff format --check .
pytest
python -m build
twine check dist/*
check-wheel-contents dist/*.whl
```

## License

MIT. See [LICENSE](LICENSE).
