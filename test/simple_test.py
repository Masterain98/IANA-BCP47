from iana_bcp47.validator import validate_bcp47

# Example Usage
if __name__ == "__main__":
    # Test cases
    test_tags = [
        "en",          # Valid language
        "en-US",       # Valid language-region
        "zh-Hant",     # Valid language-script
        "zh-Hant-CN",  # Valid language-script-region
        "sl-rozaj",    # Valid language-variant
        "de-1996",     # Valid language-variant
        "en-x-private", # Invalid tag (no support for private-use)
        "invalid-tag",  # Invalid tag
    ]

    for lang_tag in test_tags:
        result = validate_bcp47(lang_tag)
        print(f"Tag '{lang_tag}' is {'valid: ' + result if result else 'invalid'}.")