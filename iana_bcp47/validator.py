from iana_bcp47.bcp47 import language_codes, extlang_codes, script_codes, region_codes, variant_codes, redundant_codes

def validate_bcp47(tag) -> str | None:
    """
    Validate a BCP47 language tag based on the dictionaries and rules.
    Args:
        tag (str): The language tag to validate.
    Returns:
        Description of the tag if valid or None if invalid.
    """
    full_description = ""

    # Check if the tag matches any redundant cases
    if tag in redundant_codes:
        return redundant_codes[tag]

    # Split the tag into subtags
    subtags = tag.split('-')

    if not subtags:
        return None

    # Validate the primary language subtag (must be the first)
    primary_language = subtags.pop(0)
    if primary_language not in language_codes:
        return None

    # Append the description of the primary language
    full_description += language_codes[primary_language]

    # Validate remaining subtags
    for subtag in subtags:
        if subtag in extlang_codes:
            full_description += f" - {extlang_codes[subtag]}"
        elif subtag in script_codes:
            full_description += f" - {script_codes[subtag]}"
        elif subtag in region_codes:
            full_description += f" - {region_codes[subtag]}"
        elif subtag in variant_codes:
            full_description += f" - {variant_codes[subtag]}"
        else:
            # Invalid subtag
            return None

    return full_description
