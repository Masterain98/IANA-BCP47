import httpx
import json

from collections import defaultdict


# URL of the IANA language subtag registry
url = "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry"

def parse_language_subtag_registry(data: str) -> list:
    """
    Parse the IANA language subtag registry file into a structured dictionary.
    """
    entries = []
    entry = {}

    for line in data.splitlines():
        # Skip comments or empty lines
        if not line or line.startswith("%%"):
            # If there's an existing entry, save it before starting a new one
            if entry:
                entries.append(entry)
                entry = {}
            continue

        # Parse key-value pairs
        if ": " in line:
            key, value = line.split(": ", 1)
            if key in entry:
                # Convert to list if there are multiple entries for the same key
                if isinstance(entry[key], list):
                    entry[key].append(value)
                else:
                    entry[key] = [entry[key], value]
            else:
                entry[key] = value
        else:
            # Handle multi-line values for the last key
            if entry:
                last_key = list(entry.keys())[-1]
                entry[last_key] += f" {line.strip()}"

    # Append the last entry
    if entry:
        entries.append(entry)

    return entries


def filter_and_restrict_entries(entries: list) -> tuple:
    """
    Filter and restrict entries based on specific conditions:
    1. Only keep specified types and keys.
    2. Exclude entries with 'Deprecated'.
    """
    allowed_types = {'language', 'extlang', 'script', 'region', 'variant', 'redundant'}
    keys_to_keep = {'Type', 'Tag', 'Description', 'Subtag'}

    filtered_entries = []
    all_types_set = set()

    for entry in entries:
        # Collect all types
        if 'Type' in entry:
            all_types_set.add(entry['Type'])

        # Keep only entries with allowed types
        if entry.get('Type') in allowed_types:
            # Exclude deprecated entries
            if 'Deprecated' in entry:
                continue

            # Only keep specified keys
            filtered_entry = {key: value for key, value in entry.items() if key in keys_to_keep}
            filtered_entries.append(filtered_entry)

    return filtered_entries, sorted(all_types_set)


def fetch_and_save_registry() -> None:
    """
    Fetch the IANA language subtag registry file and save it to a text file.
    :return: Void
    """
    response = httpx.get(url)
    if response.status_code == 200:
        raw_data = response.text
        parsed_entries = parse_language_subtag_registry(raw_data)
        filtered_data, all_types = filter_and_restrict_entries(parsed_entries)
        with open("language-subtag-registry.txt", "w", encoding="utf-8") as f:
            f.write(raw_data)

        # Save the filtered data to a JSON file
        with open("bcp47.json", "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)

        type_dicts = defaultdict(dict)

        for entry in filtered_data:
            entry_type = entry.get("Type")
            key = entry.get("Subtag", entry.get("Tag"))
            description = entry.get("Description", "No description available")
            if isinstance(description, list):  # Join multiple descriptions
                description = " ".join(description)
            description = description.replace("'", "\\'")  # Escape single quotes
            if entry_type and key:
                type_dicts[entry_type][key] = description

        # Save the dictionaries to a Python module
        with open("bcp47.py", "w", encoding="utf-8") as py_file:
            py_file.write("# Generated Python module containing language codes by type\n\n")
            for type_name, type_dict in type_dicts.items():
                py_file.write(f"{type_name}_codes = {{\n")
                for key, description in type_dict.items():
                    py_file.write(f"    '{key}': '{description}',\n")
                py_file.write("}\n\n")

        print("Successfully fetched and saved the registry file.")
    else:
        print("Failed to fetch the registry file.")

if __name__ == "__main__":
    fetch_and_save_registry()
