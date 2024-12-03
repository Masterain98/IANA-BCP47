from iana_bcp47.bcp47 import language_codes, extlang_codes, script_codes, region_codes, variant_codes, redundant_codes


def validate_bcp47(tag: str) -> tuple[bool, str]:
    """
    Validate a BCP 47 language tag and return a description of the tag.

    :param tag: The BCP 47 language tag to validate.

    :return: A tuple containing a boolean indicating if the tag is valid and a description of the tag;
             if the tag is invalid, the description will contain an error message.
    """
    full_description = ""

    # Check if the tag matches any redundant cases
    if tag in redundant_codes:
        return redundant_codes[tag]

    # Split the tag into subtags
    subtags = tag.split('-')

    if not subtags:
        return False, "Not a valid language tag."

    # Validate the primary language subtag (must be the first)
    primary_language = subtags.pop(0)
    if primary_language not in language_codes:
        return False, f"{primary_language} is not a valid primary language."

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
            return False, f"{subtag} is not a valid subtag."

    return True, full_description
