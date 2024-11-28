from iana_bcp47.validator import validate_bcp47


if __name__ == "__main__":
    # Example usage
    tags = ["en", "en-US", "zh-Hant", "zh-Hant-CN", "invalid-tag"]

    for tag in tags:
        result = validate_bcp47(tag)
        print(f"Tag '{tag}' is {'valid: ' + result if result else 'invalid'}.")
