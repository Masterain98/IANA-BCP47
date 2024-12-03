from iana_bcp47.validator import validate_bcp47


if __name__ == "__main__":
    # Example usage
    tags = ["en", "en-US", "zh-Hant", "zh-Hant-CN", "invalid-tag", 'zh-US']

    for tag in tags:
        valid, msg = validate_bcp47(tag)
        print(f"Tag '{tag}' is {'valid: ' + msg if valid else 'invalid'}.")
