#!/usr/bin/python3

import json
from pathlib import Path
from typing import Any, TypeAlias

DataEntry: TypeAlias = dict[str, Any]
Component: TypeAlias = list[Any]
ComponentsList: TypeAlias = list[Component]


# TODO make this load from a JSON config file
def load_config() -> dict[str, str]:
    """
    Loads configuration paths, replacing hardcoded values.

    :returns: A dictionary mapping configuration names to their file system paths.
    :rtype: dict[str, str]
    """
    return {
        "LTPROJ_FOLDER": "FE8R.ltproj",
        "RESULTS_FOLDER": "Results",
    }


CONFIG = load_config()
LTPROJ_FOLDER = Path(CONFIG["LTPROJ_FOLDER"])
RESULTS_FOLDER = Path(CONFIG["RESULTS_FOLDER"])

EXCLUDE: tuple[str, ...] = (
    "_hide",
    "_Penalty",
    "_Gain",
    "_Proc",
    "_Weapon",
    "_AOE_Splash",
    "_Boss",
    "Avo_Ddg_",
)


def get_component(entry: DataEntry, comp_name: str, comp_type: type) -> Any:
    """
    Retrieves the value of a component from an entry.
    Returns a default value based on comp_type if the component is not found.

    :param entry: The item data entry dictionary to search within.
    :type entry: DataEntry
    :param comp_name: The string name of the component to find (e.g., 'status_on_equip').
    :type comp_name: str
    :param comp_type: The expected type of the component's value (e.g., str, list, bool).
    :type comp_type: type
    :returns: The component's value, or a type-appropriate default.
    :rtype: Any
    """
    default_values: dict[type, Any] = {
        bool: False,
        int: 0,
        str: "",
        list: [],
    }

    comp_entry: list[Any] | None = next(
        (x for x in entry.get("components", []) if x[0] == comp_name), None
    )

    if comp_entry:
        value = comp_entry[1]
        if comp_type is bool and value is None:
            return True
        return value

    if comp_type is bool:
        return False
    return default_values.get(comp_type, None)


def get_status(data_entry: DataEntry) -> list[str]:
    """
    Extracts unique, non-excluded status names from various component fields of an entry.

    :param data_entry: The item data entry to process.
    :type data_entry: DataEntry
    :returns: A list of unique status names associated with the item, excluding any in EXCLUDE.
    :rtype: list[str]
    """
    excluded_substrings: tuple[str, ...] = EXCLUDE
    wp_status: set[str] = set()

    single_status_comps: tuple[str, ...] = ("status_on_equip", "status_on_hit")
    multi_status_comps: tuple[str, ...] = ("multi_status_on_equip", "statuses_on_hit")

    # Process single status components
    for comp_name in single_status_comps:
        status: str = get_component(data_entry, comp_name, str)
        if status and not any(sub in status for sub in excluded_substrings):
            wp_status.add(status)

    # Process multi-status components
    for comp_name in multi_status_comps:
        statuses: list[str] = get_component(data_entry, comp_name, list)
        for status_entry in statuses:
            if status_entry and not any(
                sub in status_entry for sub in excluded_substrings
            ):
                wp_status.add(status_entry)

    return list(wp_status)


def add_multi_desc() -> None:
    """
    Reads all JSON files, extracts relevant statuses using `get_status`,
    and adds or updates the 'multi_desc_skill' component in each item entry.

    The updated item data is saved to a new location specified by RESULTS_FOLDER.
    """
    ltproj_path: Path = LTPROJ_FOLDER
    results_path: Path = RESULTS_FOLDER

    if not results_path.exists():
        results_path.mkdir(exist_ok=True)

    new_items_folder: Path = results_path / "items"
    new_items_folder.mkdir(exist_ok=True)
    items_data_path: Path = ltproj_path / "game_data" / "items"

    for item_json in items_data_path.iterdir():
        if item_json.suffix == ".json":
            with item_json.open("r", encoding="utf-8") as fp:
                try:
                    data_entries: list[DataEntry] = json.load(fp)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in {item_json.name}: {e}")
                    continue

            for data_entry in data_entries:
                print(f"Adding to {data_entry["nid"]} ...")
                extracted_stats: list[str] = get_status(data_entry)

                if extracted_stats:
                    existing_value = get_component(data_entry, "multi_desc_skill", list)

                    new_value: list[str]
                    if isinstance(existing_value, list):
                        new_value = list(
                            dict.fromkeys(existing_value + extracted_stats)
                        )
                    else:
                        new_value = extracted_stats

                    # Update or add the 'multi_desc_skill' component
                    new_components: ComponentsList = [
                        x
                        for x in data_entry.get("components", [])
                        if x[0] != "multi_desc_skill"
                    ]
                    new_components.append(["multi_desc_skill", new_value])
                    data_entry["components"] = new_components

                    # Save the updated entry
                    new_item = [data_entry]
                    with (new_items_folder / item_json.name).open(
                        "w", encoding="utf-8"
                    ) as fp:
                        json.dump(new_item, fp, indent=4)
    print("Done.")


def main() -> None:
    add_multi_desc()


if __name__ == "__main__":
    main()
