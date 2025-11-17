import json
from pathlib import Path
from typing import Any

# The slashes might be backslash in windows
LTPROJ_JSON_FOLDER = Path("/Users/Garrett Fuller/Desktop/Test/FE8R.ltproj")
RESULTS_FOLDER = Path("/Users/Garrett Fuller/Desktop/Results")
EXCLUDE: tuple = (
    "_hide",
    "_Penalty",
    "_Gain",
    "_Proc",
    "_Weapon",
    "_AOE_Splash",
    "_Boss"
    "Avo_Ddg_",
    "Luckblade",
)


def _get_status_equip(data_entry) -> list:
    exclude = EXCLUDE
    wp_status = []

    # --- status_on_equip (single) ---
    if s1 := get_comp(data_entry, "status_on_equip", str):
        if not any(sub in s1 for sub in exclude):
            wp_status.append(s1)

    # --- multi_status_on_equip (list) ---
    if s2 := get_comp(data_entry, "multi_status_on_equip", list):
        for entry in s2:
            if not any(sub in entry for sub in exclude):
                wp_status.append(entry)

    # --- status_on_hit (single) ---
    if s3 := get_comp(data_entry, "status_on_hit", str):
        if not any(sub in s3 for sub in exclude):
            wp_status.append(s3)

    # --- statuses_on_hit (list) ---
    if s4 := get_comp(data_entry, "statuses_on_hit", list):
        for entry in s4:
            if not any(sub in entry for sub in exclude):
                wp_status.append(entry)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(wp_status))


def get_comp(entry, comp_name: str, comp_type: type) -> Any:
    """
    Returns component value
    """
    if comp_entry := [x for x in entry["components"] if x[0] == comp_name]:
        if comp_type == bool:
            if comp_entry[0][1] is None:
                return True
        else:
            return comp_entry[0][1]
    if comp_type == bool:
        return False
    elif comp_type == int:
        return 0
    elif comp_type == str:
        return ""
    elif comp_type == list:
        return []
    return None


def add_multi_desc():
    new_items_folder = RESULTS_FOLDER / "items"
    new_items_folder.mkdir(exist_ok=True)
    for item_json in (LTPROJ_JSON_FOLDER / "game_data" / "items").iterdir():
        if item_json.suffix == ".json":
            with item_json.open("r") as fp:
                for data_entry in json.load(fp):
                    print(data_entry["nid"])
                    if stats := _get_status_equip(data_entry):
                        if not get_comp(data_entry, "multi_desc_skill", bool):
                            data_entry["components"].append(["multi_desc_skill", stats])
                        else:
                            new_components = [
                                x
                                for x in data_entry["components"]
                                if x[0] != "multi_desc_skill"
                            ]
                            new_components.append(
                                [
                                    "multi_desc_skill",
                                    get_comp(data_entry, "multi_desc_skill", bool)
                                    + stats,
                                ]
                            )
                            data_entry["components"] = new_components
                        new_item = [data_entry]
                        with (new_items_folder / item_json.name).open(
                            "w", encoding="utf-8"
                        ) as fp:
                            json.dump(new_item, fp, indent=4)


def main():
    add_multi_desc()


if __name__ == "__main__":
    main()
