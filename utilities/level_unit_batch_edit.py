import json
import re
from pathlib import Path

import FreeSimpleGUI as sg

CONFIG_FILE = Path("level_unit_batch_edit_config.json")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config: dict) -> None:
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        sg.popup_error(f"Failed to save configuration file: {e}")


def load_item_nids(file_path: Path) -> set:
    item_nids: set = set()
    if not file_path.exists():
        return item_nids

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "nid" in item:
                        item_nids.add(item["nid"])
            sg.popup_quick_message(
                f"Successfully loaded {len(item_nids)} item nids for validation."
            )
    except Exception as e:
        sg.popup_error(f"Failed to load item nids from {file_path.name}:\n{e}")
        return set()

    return item_nids


def natural_sort_key(s: str) -> list:
    return [
        int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)
    ]


def load_chapter_data(levels_dir: Path) -> dict:
    chapter_data: dict = {}
    if not levels_dir.exists():
        return {}

    for file_path in levels_dir.glob("*.json"):
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

                if (
                    isinstance(data, list)
                    and data
                    and "units" in data[0]
                    and data[0].get("units")
                ):
                    chapter_data[file_path.name] = json.loads(json.dumps(data))
        except Exception:
            continue
    return chapter_data


def get_unit_info(chapter_data: list, unit_nids: list) -> dict:
    if not chapter_data or not unit_nids:
        return {}

    unit_infos: dict = {}
    chapter = chapter_data[0]

    for unit_data in chapter.get("units", []):
        nid = unit_data.get("nid")
        if nid in unit_nids:
            items: list = []
            raw_items_copy: list = [
                list(item) for item in unit_data.get("starting_items", [])
            ]
            for item_list in raw_items_copy:
                item_nid = item_list[0]
                is_droppable = item_list[1]

                display_string = item_nid
                if is_droppable:
                    display_string += " (Droppable)"
                items.append(display_string)

            unit_infos[nid] = {
                "items": items,
                "raw_items": raw_items_copy,
            }

    return unit_infos


def get_all_unit_nids(chapter_data: list) -> list:
    if not chapter_data:
        return []

    chapter = chapter_data[0]
    unit_list = [
        f"{unit.get('nid')} ({unit.get('klass')})"
        for unit in chapter.get("units", [])
        if unit.get("nid") and unit.get("klass") != "Wall25"
    ]
    return sorted(unit_list)


def update_chapter_file(file_path: Path, chapter_data: list) -> bool:
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=4)
        return True
    except Exception as e:
        sg.popup_error(f"Failed to save file:\n{e}")
        return False


def create_layout(initial_ltproj_dir: str, initial_items_file_path: str) -> list:
    left_column = [
        [sg.Text("LT Project Directory:")],
        [
            sg.Input(
                key="-LTPROJ_DIR-",
                enable_events=True,
                size=35,
                default_text=initial_ltproj_dir,
            ),
            sg.FolderBrowse(target="-LTPROJ_DIR-"),
        ],
        [sg.Text("items.json File Path (for validation):")],
        [
            sg.Input(
                key="-ITEMS_FILE_PATH-",
                enable_events=True,
                size=35,
                default_text=initial_items_file_path,
            ),
            sg.FileBrowse(
                target="-ITEMS_FILE_PATH-", file_types=(("JSON Files", "*.json"),)
            ),
        ],
        [sg.Text("Select Chapter File:")],
        [
            sg.Combo(
                values=[],
                key="-CHAPTER_FILE-",
                enable_events=True,
                size=35,
                readonly=True,
            )
        ],
        [sg.Text("Select Units (Ctrl/Shift for multi-select):")],
        [
            sg.Listbox(
                values=[],
                key="-UNIT_LIST-",
                size=(35, 20),
                select_mode=sg.SELECT_MODE_EXTENDED,
                enable_events=True,
            )
        ],
        [
            sg.Button(
                "Select Units by Same Class",
                key="-SELECT_BY_CLASS-",
                disabled=True,
            )
        ],
    ]

    right_column = [
        [sg.Text("Starting Items for Selected Units:")],
        [
            sg.Listbox(
                values=[],
                key="-ITEM_LIST-",
                size=(45, 10),
                select_mode=sg.SELECT_MODE_SINGLE,
                enable_events=True,
            )
        ],
        [sg.Button("Copy Item nid to Input", key="-COPY_ITEM_NID-", disabled=True)],
        [
            sg.Checkbox(
                "Validate new item nid",
                key="-VALIDATE_NID-",
                default=True,
            )
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Item nid to Add/Delete:")],
        [
            sg.Input(key="-ITEM_NID-", size=20, default_text=""),
            sg.Checkbox("Droppable", key="-Droppable-", default=False),
        ],
        [
            sg.Button("Add Item", key="-ADD_ITEM-", disabled=True),
        ],
        [
            sg.Button(
                "Delete Item", key="-DELETE_ITEM-", disabled=True, button_color="red"
            )
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Item nid to replace:")],
        [
            sg.Input(key="-OLD_ITEM_NID-", size=20, default_text=""),
        ],
        [sg.Text("New item nid:")],
        [
            sg.Input(key="-NEW_ITEM_NID-", size=20, default_text=""),
            sg.Checkbox("Droppable", key="-NEW_Droppable-", default=False),
        ],
        [
            sg.Button(
                "Replace Item",
                key="-REPLACE_ITEM-",
                disabled=True,
                button_color="orange",
            )
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button(
                "Save Changes",
                key="-SAVE_CHANGES-",
                disabled=True,
                button_color="green",
            ),
            sg.Button("Reset", key="-RESET-", disabled=True, button_color="red"),
        ],
    ]

    layout = [
        [sg.Column(left_column), sg.Column(right_column)],
        [sg.Push(), sg.Button("Exit")],
    ]

    return layout


def main() -> None:
    config = load_config()
    initial_ltproj_dir: str = config.get("ltproj_dir", "")
    initial_items_file_path: str = config.get("items_file_path", "")

    window = sg.Window(
        "Chapter Unit Item Batch Editor",
        create_layout(initial_ltproj_dir, initial_items_file_path),
        finalize=True,
    )

    current_ltproj_dir: str = initial_ltproj_dir
    current_chapter_file: str = ""
    chapter_data_map: dict = {}
    current_unit_info: dict = {}
    current_items_file_path: str = initial_items_file_path
    current_items_nids: set = set()

    original_chapter_data: list = []

    def has_unsaved_changes() -> bool:
        if not current_chapter_file or not original_chapter_data:
            return False

        current_data = chapter_data_map.get(current_chapter_file)
        if not current_data:
            return False

        return json.dumps(current_data, sort_keys=True) != json.dumps(
            original_chapter_data, sort_keys=True
        )

    if current_ltproj_dir:
        levels_dir = Path(current_ltproj_dir) / "game_data" / "levels"
        if levels_dir.exists():
            chapter_data_map = load_chapter_data(levels_dir)
            chapter_files = sorted(chapter_data_map.keys(), key=natural_sort_key)
            window["-CHAPTER_FILE-"].update(values=chapter_files)

    if current_items_file_path:
        path = Path(current_items_file_path)
        if path.exists():
            current_items_nids = load_item_nids(path)

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit"):
            if current_chapter_file and has_unsaved_changes():
                response = sg.popup_yes_no(
                    f"You have unsaved changes in {current_chapter_file}. Exit and discard changes?"
                )
                if response != "Yes":
                    continue
            break

        if event == "-ITEMS_FILE_PATH-":
            new_items_file_path: str = values["-ITEMS_FILE_PATH-"]
            current_items_file_path = new_items_file_path

            if new_items_file_path:
                config["items_file_path"] = new_items_file_path
                save_config(config)

            path = Path(current_items_file_path)
            if path.exists():
                current_items_nids = load_item_nids(path)
            else:
                current_items_nids = set()
                sg.popup_quick_message("Items file not found or path is invalid.")

        elif event == "-LTPROJ_DIR-":
            new_ltproj_dir: str = values["-LTPROJ_DIR-"]

            if current_chapter_file and has_unsaved_changes():
                response = sg.popup_yes_no(
                    f"You have unsaved changes in {current_chapter_file}. Discard and change directory?"
                )
                if response != "Yes":
                    window["-LTPROJ_DIR-"].update(current_ltproj_dir)
                    continue

            if new_ltproj_dir:
                config["ltproj_dir"] = new_ltproj_dir
                save_config(config)

            current_ltproj_dir = new_ltproj_dir
            levels_dir = Path(current_ltproj_dir) / "game_data" / "levels"

            window["-CHAPTER_FILE-"].update(values=[], value="")
            window["-UNIT_LIST-"].update(values=[])
            window["-ITEM_LIST-"].update(values=[])
            window["-ADD_ITEM-"].update(disabled=True)
            window["-DELETE_ITEM-"].update(disabled=True)
            window["-SAVE_CHANGES-"].update(disabled=True)
            window["-COPY_ITEM_NID-"].update(disabled=True)
            window["-SELECT_BY_CLASS-"].update(disabled=True)
            window["-REPLACE_ITEM-"].update(disabled=True)
            window["-RESET-"].update(disabled=True)

            current_chapter_file = ""
            current_unit_info = {}
            original_chapter_data = []

            if levels_dir.exists():
                chapter_data_map = load_chapter_data(levels_dir)
                chapter_files = sorted(chapter_data_map.keys(), key=natural_sort_key)
                window["-CHAPTER_FILE-"].update(values=chapter_files)
                if chapter_files:
                    sg.popup_quick_message(
                        f"Found {len(chapter_files)} valid chapter files.",
                    )
            else:
                sg.popup_quick_message(
                    "Levels directory not found.",
                )

        elif event == "-CHAPTER_FILE-" and values["-CHAPTER_FILE-"]:
            new_chapter_file: str = values["-CHAPTER_FILE-"]

            if current_chapter_file and has_unsaved_changes():
                response = sg.popup_yes_no(
                    f"You have unsaved changes in {current_chapter_file}. Discard and load {new_chapter_file}?"
                )
                if response != "Yes":
                    window["-CHAPTER_FILE-"].update(value=current_chapter_file)
                    continue

            current_chapter_file = new_chapter_file

            window["-UNIT_LIST-"].update(values=[], set_to_index=[])
            window["-ITEM_LIST-"].update(values=[])
            window["-ADD_ITEM-"].update(disabled=True)
            window["-DELETE_ITEM-"].update(disabled=True)
            window["-SAVE_CHANGES-"].update(disabled=True)
            window["-COPY_ITEM_NID-"].update(disabled=True)
            window["-SELECT_BY_CLASS-"].update(disabled=True)
            window["-REPLACE_ITEM-"].update(disabled=True)
            window["-RESET-"].update(disabled=True)

            current_unit_info = {}
            original_chapter_data = []

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if current_chapter_data:
                original_chapter_data = json.loads(json.dumps(current_chapter_data))
                window["-RESET-"].update(disabled=False)

                all_unit_nids_and_klass = get_all_unit_nids(current_chapter_data)
                window["-UNIT_LIST-"].update(values=all_unit_nids_and_klass)

        elif event == "-UNIT_LIST-" and values["-UNIT_LIST-"]:
            selected_unit_strings: list = values["-UNIT_LIST-"]

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            current_chapter_data = chapter_data_map.get(current_chapter_file)

            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)

            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])

            window["-ITEM_LIST-"].update(values=display_items)
            window["-ADD_ITEM-"].update(disabled=False)
            window["-DELETE_ITEM-"].update(disabled=False)
            window["-SAVE_CHANGES-"].update(disabled=False)
            window["-COPY_ITEM_NID-"].update(disabled=False)
            window["-SELECT_BY_CLASS-"].update(disabled=False)
            window["-REPLACE_ITEM-"].update(disabled=False)

            if not values["-ITEM_LIST-"]:
                window["-COPY_ITEM_NID-"].update(disabled=True)

        elif event == "-SELECT_BY_CLASS-":
            selected_unit_strings: list = values["-UNIT_LIST-"]

            if not selected_unit_strings:
                sg.popup_quick_message(
                    "Please select at least one unit to use as a class filter."
                )
                continue

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if not current_chapter_data:
                sg.popup_quick_message("No chapter data loaded.")
                continue

            target_classes: set = set()
            for unit_str in selected_unit_strings:
                match = re.search(r"\((.*?)\)$", unit_str)
                if match:
                    target_classes.add(match.group(1))

            if not target_classes:
                sg.popup_quick_message(
                    "Could not determine class(es) from selected units."
                )
                continue

            all_unit_strings: list = window["-UNIT_LIST-"].get_list_values()
            indices_to_select: list = []

            for i, unit_str in enumerate(all_unit_strings):
                match = re.search(r"\((.*?)\)$", unit_str)
                if match and match.group(1) in target_classes:
                    indices_to_select.append(i)

            if indices_to_select:
                window["-UNIT_LIST-"].update(set_to_index=indices_to_select)

                window.write_event_value("-UNIT_LIST-", window["-UNIT_LIST-"].get())
                sg.popup_quick_message(
                    f"Selected {len(indices_to_select)} unit(s) with class(es): {', '.join(target_classes)}"
                )
            else:
                sg.popup_quick_message("No units found with the same class(es).")

        elif event == "-ITEM_LIST-" and values["-ITEM_LIST-"]:
            window["-COPY_ITEM_NID-"].update(disabled=False)

        elif event == "-COPY_ITEM_NID-":
            selected_items: list = values["-ITEM_LIST-"]
            if selected_items:
                item_string = selected_items[0]
                item_nid = item_string.split(" ")[0]

                window["-ITEM_NID-"].update(value=item_nid)
                window["-OLD_ITEM_NID-"].update(value=item_nid)
                window["-NEW_ITEM_NID-"].update(value="")
                sg.popup_quick_message(f"Copied item nid: '{item_nid}'")
            else:
                sg.popup_quick_message("Please select an item to copy its nid.")

        elif event == "-ADD_ITEM-":
            new_item_nid: str = values["-ITEM_NID-"].strip()
            is_droppable: bool = values["-Droppable-"]
            selected_unit_strings: list = values["-UNIT_LIST-"]

            if not new_item_nid:
                sg.popup_quick_message("Please enter a valid item nid.")
                continue

            if not selected_unit_strings:
                sg.popup_quick_message(
                    "Please select at least one unit to add the item to."
                )
                continue

            validate_nid: bool = values["-VALIDATE_NID-"]
            if validate_nid:
                if not current_items_nids:
                    if (
                        sg.popup_yes_no(
                            "items.json not loaded. Add item without validation?"
                        )
                        == "No"
                    ):
                        continue

                elif new_item_nid not in current_items_nids:
                    if (
                        sg.popup_yes_no(
                            f"Item nid '{new_item_nid}' not found in the loaded items.json file. Add item anyway?"
                        )
                        == "No"
                    ):
                        continue

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if not current_chapter_data:
                sg.popup_quick_message("Chapter data not loaded. Cannot add item.")
                continue

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            new_item_raw: list = [new_item_nid, is_droppable]

            for nid in selected_unit_nids:
                unit_data = current_unit_info[nid]
                if new_item_raw not in unit_data["raw_items"]:
                    unit_data["raw_items"].append(new_item_raw)

            chapter_object = current_chapter_data[0]
            for unit in chapter_object["units"]:
                nid = unit.get("nid")
                if nid in current_unit_info:
                    unit["starting_items"] = current_unit_info[nid]["raw_items"]

            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)
            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])
            window["-ITEM_LIST-"].update(values=display_items)
            window["-COPY_ITEM_NID-"].update(disabled=True)

            sg.popup_quick_message(
                f"Added {new_item_nid} to {len(selected_unit_nids)} unit(s).",
            )

        elif event == "-DELETE_ITEM-":
            item_nid_to_delete: str = values["-ITEM_NID-"].strip()
            is_droppable_filter: bool = values["-Droppable-"]
            selected_unit_strings: list = values["-UNIT_LIST-"]

            if not item_nid_to_delete:
                sg.popup_quick_message("Please enter the item nid you wish to delete.")
                continue

            if not selected_unit_strings:
                sg.popup_quick_message("Please select at least one unit.")
                continue

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if not current_chapter_data:
                sg.popup_quick_message("Chapter data not loaded. Cannot delete item.")
                continue

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            units_modified_count: int = 0

            for nid in selected_unit_nids:
                unit_data = current_unit_info[nid]
                raw_items = unit_data["raw_items"]
                initial_count = len(raw_items)

                if is_droppable_filter:
                    item_to_delete: list = [item_nid_to_delete, is_droppable_filter]
                    raw_items[:] = [
                        item for item in raw_items if item != item_to_delete
                    ]
                else:
                    raw_items[:] = [
                        item for item in raw_items if item[0] != item_nid_to_delete
                    ]

                if len(raw_items) < initial_count:
                    units_modified_count += 1

            chapter_object = current_chapter_data[0]
            for unit in chapter_object["units"]:
                nid = unit.get("nid")
                if nid in current_unit_info:
                    unit["starting_items"] = current_unit_info[nid]["raw_items"]

            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)
            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])
            window["-ITEM_LIST-"].update(values=display_items)
            window["-COPY_ITEM_NID-"].update(disabled=True)

            if units_modified_count > 0:
                sg.popup_quick_message(
                    f"Deleted {item_nid_to_delete} from {units_modified_count} unit(s).",
                )
            else:
                sg.popup_quick_message(
                    f"Item {item_nid_to_delete} not found on selected units.",
                )

        elif event == "-REPLACE_ITEM-":
            item_nid_to_find: str = values["-OLD_ITEM_NID-"].strip()

            new_item_nid: str = values["-NEW_ITEM_NID-"].strip()
            is_droppable_new: bool = values["-NEW_Droppable-"]

            selected_unit_strings: list = values["-UNIT_LIST-"]

            if not item_nid_to_find:
                sg.popup_quick_message("Please enter the 'Item nid to replace'.")
                continue
            if not new_item_nid:
                sg.popup_quick_message("Please enter the 'New item nid'.")
                continue
            if not selected_unit_strings:
                sg.popup_quick_message("Please select at least one unit.")
                continue

            if item_nid_to_find == new_item_nid:
                sg.popup_quick_message(
                    "The old and new item nids are identical. No action taken."
                )
                continue

            validate_nid: bool = values["-VALIDATE_NID-"]
            if validate_nid:
                if not current_items_nids:
                    if (
                        sg.popup_yes_no(
                            "items.json not loaded. Continue with replacement?"
                        )
                        == "No"
                    ):
                        continue
                elif new_item_nid not in current_items_nids:
                    if (
                        sg.popup_yes_no(
                            f"Replacement item nid '{new_item_nid}' not found in the loaded items.json file. Replace anyway?"
                        )
                        == "No"
                    ):
                        continue

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if not current_chapter_data:
                sg.popup_quick_message("Chapter data not loaded. Cannot replace item.")
                continue

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            replacement_item_raw: list = [new_item_nid, is_droppable_new]

            units_modified_count: int = 0

            for nid in selected_unit_nids:
                unit_data = current_unit_info[nid]
                raw_items = unit_data["raw_items"]
                modified: bool = False

                for i, raw_item in enumerate(raw_items):
                    item = raw_item

                    if item[0] == item_nid_to_find:
                        raw_items[i] = replacement_item_raw
                        modified = True

                if modified:
                    units_modified_count += 1

            chapter_object = current_chapter_data[0]
            for unit in chapter_object["units"]:
                nid = unit.get("nid")
                if nid in current_unit_info:
                    unit["starting_items"] = current_unit_info[nid]["raw_items"]

            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)
            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])
            window["-ITEM_LIST-"].update(values=display_items)
            window["-COPY_ITEM_NID-"].update(disabled=True)

            if units_modified_count > 0:
                sg.popup_quick_message(
                    f"Replaced all instances of '{item_nid_to_find}' with '{new_item_nid}' (Droppable: {is_droppable_new}) in {units_modified_count} unit(s).",
                )
            else:
                sg.popup_quick_message(
                    f"Item '{item_nid_to_find}' not found on selected units for replacement.",
                )

        elif event == "-RESET-":
            if not original_chapter_data:
                sg.popup_quick_message("No original chapter data available to reset.")
                continue

            if (
                sg.popup_yes_no(
                    "Are you sure you want to revert ALL unsaved changes for this chapter to the original loaded state?"
                )
                == "Yes"
            ):
                current_chapter_data_reset: list = json.loads(
                    json.dumps(original_chapter_data)
                )
                chapter_data_map[current_chapter_file] = current_chapter_data_reset

                selected_unit_strings: list = values["-UNIT_LIST-"]
                selected_unit_nids = [
                    unit_str.split(" ")[0] for unit_str in selected_unit_strings
                ]
                current_unit_info = get_unit_info(
                    current_chapter_data_reset, selected_unit_nids
                )

                first_unit_nid = selected_unit_nids[0] if selected_unit_nids else None
                display_items = (
                    current_unit_info.get(first_unit_nid, {}).get("items", [])
                    if first_unit_nid
                    else []
                )
                window["-ITEM_LIST-"].update(values=display_items)

                sg.popup_quick_message("Chapter data reset to original loaded state.")

        elif event == "-SAVE_CHANGES-":
            if not current_chapter_file:
                sg.popup_quick_message("No chapter selected to save.")
                continue

            file_path = (
                Path(current_ltproj_dir) / "game_data" / "levels" / current_chapter_file
            )
            chapter_data = chapter_data_map.get(current_chapter_file)

            if not chapter_data:
                sg.popup_error("Chapter data not found in memory. Cannot save.")
                continue

            chapter_object = chapter_data[0]
            for unit in chapter_object["units"]:
                nid = unit.get("nid")
                if nid in current_unit_info:
                    unit["starting_items"] = current_unit_info[nid]["raw_items"]

            if update_chapter_file(file_path, chapter_data):
                sg.popup_ok(f"Successfully saved changes to {current_chapter_file}!")

                levels_dir = Path(current_ltproj_dir) / "game_data" / "levels"
                chapter_data_map = load_chapter_data(levels_dir)
                current_chapter_data = chapter_data_map.get(current_chapter_file)

                if current_chapter_data:
                    original_chapter_data = json.loads(json.dumps(current_chapter_data))

            else:
                sg.popup_error(f"Failed to save changes to {current_chapter_file}.")

    window.close()


if __name__ == "__main__":
    main()
