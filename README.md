# IANA-BCP47 (BCP47 Validator)

This project provides a Python implementation of a [BCP47](https://tools.ietf.org/html/bcp47) language tag validator. It validates language tags based on the IANA Language Subtag Registry and ensures compliance with BCP47 specifications. The validator supports checking for redundant tags and validating custom language codes using dictionaries of subtags.

## Features

- Validates BCP47 language tags with dictionaries derived from the IANA Language Subtag Registry.
- Supports validation for the following subtag types:
  - `language`
  - `extlang`
  - `script`
  - `region`
  - `variant`
  - `redundant`
- Provides detailed descriptions of valid language tags.
- **Returns `None` for invalid tags.**

## How It Works

The project uses a generated Python module (`bcp47.py`) containing dictionaries for each type of subtag. Each language tag is validated as follows:
1. The first subtag must match a valid language code.
2. Subsequent subtags are validated against dictionaries for `extlang`, `script`, `region`, and `variant`.
3. Redundant tags (full language tags) are checked separately.
4. Return a tuple with two elements:
    - The first element is a boolean indicating whether the tag is valid.
    - The second element is a string describing the language tag or error message if the tag is invalid.

## Usage

> [!IMPORTANT]
>
> The IANA-BCP47 library validates whether a given string conforms to the BCP 47 standard format. However, it does not verify whether the string represents a practical or commonly used language code. For instance, `ru-US` is a valid BCP 47 format but is not a language code typically used in real-world applications.


### Validate a BCP47 Language Tag

Use the `validate_bcp47` function to validate a language tag and retrieve its description.

```console
pip install iana-bcp47
```

```python
from iana_bcp47.validator import validate_bcp47

# Example usage
tags = ["en", "en-US", "zh-Hant", "zh-Hant-CN", "invalid-tag", 'zh-US']

for tag in tags:
    valid, msg = validate_bcp47(tag)
    print(f"Tag '{tag}' is {'valid: ' + msg if valid else 'invalid'}.")
```

### Output Example

```
Tag 'en' is valid: English.
Tag 'en-US' is valid: English - United States.
Tag 'zh-Hant' is valid: traditional Chinese.
Tag 'zh-Hant-CN' is valid: PRC Mainland Chinese in traditional script.
Tag 'invalid-tag' is invalid.
Tag 'zh-US' is valid: Chinese - United States.
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.