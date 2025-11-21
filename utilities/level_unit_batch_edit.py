import json
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


def save_config(config: dict):
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        sg.popup_error(f"Failed to save configuration file: {e}")


def load_chapter_data(levels_dir: Path) -> dict[str, list]:
    chapter_data = {}
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
                    chapter_data[file_path.name] = data
        except Exception:
            continue
    return chapter_data


def get_unit_info(chapter_data: list, unit_nids: list[str]) -> dict:
    if not chapter_data or not unit_nids:
        return {}

    unit_infos = {}
    chapter = chapter_data[0]

    for unit_data in chapter.get("units", []):
        nid = unit_data.get("nid")
        if nid in unit_nids:
            items = []
            for item_list in unit_data.get("starting_items", []):
                item_nid = item_list[0]
                is_droppable = item_list[1]
                status = "Droppable" if is_droppable else "Not Droppable"
                items.append(f"{item_nid} ({status})")

            unit_infos[nid] = {
                "items": items,
                "raw_items": unit_data.get("starting_items", []),
            }

    return unit_infos


def get_all_unit_nids(chapter_data: list) -> list[str]:
    if not chapter_data:
        return []

    chapter = chapter_data[0]
    unit_list = [
        f"{unit.get('nid')} ({unit.get('klass')})"
        for unit in chapter.get("units", [])
        if unit.get("nid") and unit.get("klass") != "Wall25"
    ]
    return sorted(unit_list)


def update_chapter_file(file_path: Path, chapter_data: list):
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=4)
        return True
    except Exception as e:
        sg.popup_error(f"Failed to save file:\n{e}")
        return False


def create_layout(initial_ltproj_dir: str):
    left_column = [
        [sg.Text("LT Project Directory:")],
        [
            sg.Input(
                key="-LTPROJ_DIR-",
                enable_events=True,
                size=(35, 1),
                default_text=initial_ltproj_dir,
            ),
            sg.FolderBrowse(target="-LTPROJ_DIR-"),
        ],
        [sg.Text("Select Chapter File:")],
        [
            sg.Combo(
                values=[],
                key="-CHAPTER_FILE-",
                enable_events=True,
                size=(35, 1),
                readonly=True,
            )
        ],
        [sg.Text("Select Units (Ctrl/Shift for multi-select):")],
        [
            sg.Listbox(
                values=[],
                key="-UNIT_LIST-",
                size=(35, 15),
                select_mode=sg.SELECT_MODE_EXTENDED,
                enable_events=True,
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
            )
        ],
        [sg.Text("Item nid to Add/Delete:")],
        [
            sg.Input(key="-ITEM_NID-", size=(20, 1), default_text="Item_nid"),
            sg.Checkbox("Droppable", key="-Droppable-", default=False),
        ],
        [
            sg.Button("Add Item", key="-ADD_ITEM-", disabled=True),
            sg.Button("Delete Item", key="-DELETE_ITEM-", disabled=True),
        ],
        [sg.Button("Save Changes", key="-SAVE_CHANGES-", disabled=True)],
    ]

    layout = [
        [sg.Column(left_column), sg.Column(right_column)],
        [sg.Push(), sg.Button("Exit")],
    ]

    return layout


def main_loop():
    config = load_config()
    initial_ltproj_dir = config.get("ltproj_dir", "")

    window = sg.Window(
        "Chapter Unit Editor", create_layout(initial_ltproj_dir), finalize=True
    )

    current_ltproj_dir = initial_ltproj_dir
    current_chapter_file = ""
    chapter_data_map = {}
    current_unit_info = {}

    if current_ltproj_dir:
        levels_dir = Path(current_ltproj_dir) / "game_data" / "levels"
        if levels_dir.exists():
            chapter_data_map = load_chapter_data(levels_dir)
            chapter_files = sorted(chapter_data_map.keys())
            window["-CHAPTER_FILE-"].update(values=chapter_files)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Exit":
            break

        if event == "-LTPROJ_DIR-":
            new_ltproj_dir = values["-LTPROJ_DIR-"]

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
            current_chapter_file = ""
            current_unit_info = {}

            if levels_dir.exists():
                chapter_data_map = load_chapter_data(levels_dir)
                chapter_files = sorted(chapter_data_map.keys())
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
            current_chapter_file = values["-CHAPTER_FILE-"]

            window["-UNIT_LIST-"].update(values=[], set_to_index=[])
            window["-ITEM_LIST-"].update(values=[])
            window["-ADD_ITEM-"].update(disabled=True)
            window["-DELETE_ITEM-"].update(disabled=True)
            window["-SAVE_CHANGES-"].update(disabled=True)
            current_unit_info = {}

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            if current_chapter_data:
                all_unit_nids_and_klass = get_all_unit_nids(current_chapter_data)
                window["-UNIT_LIST-"].update(values=all_unit_nids_and_klass)

        elif event == "-UNIT_LIST-" and values["-UNIT_LIST-"]:
            selected_unit_strings = values["-UNIT_LIST-"]

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

        elif event == "-ADD_ITEM-":
            new_item_nid = values["-ITEM_NID-"].strip()
            is_droppable = values["-Droppable-"]
            selected_unit_strings = values["-UNIT_LIST-"]

            if not new_item_nid or new_item_nid == "Item_nid":
                sg.popup_warning("Please enter a valid Item nid.")
                continue

            if not selected_unit_strings:
                sg.popup_warning("Please select at least one unit to add the item to.")
                continue

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            new_item_raw = [new_item_nid, is_droppable]

            for nid in selected_unit_nids:
                unit_data = current_unit_info[nid]
                if new_item_raw not in unit_data["raw_items"]:
                    unit_data["raw_items"].append(new_item_raw)

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)
            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])
            window["-ITEM_LIST-"].update(values=display_items)

            sg.popup_quick_message(
                f"Added {new_item_nid} to {len(selected_unit_nids)} unit(s).",
            )

        elif event == "-DELETE_ITEM-":
            item_nid_to_delete = values["-ITEM_NID-"].strip()
            is_droppable_filter = values["-Droppable-"]
            selected_unit_strings = values["-UNIT_LIST-"]

            if not item_nid_to_delete or item_nid_to_delete == "Item_nid":
                sg.popup_warning("Please enter the Item nid you wish to delete.")
                continue

            if not selected_unit_strings:
                sg.popup_warning("Please select at least one unit.")
                continue

            selected_unit_nids = [
                unit_str.split(" ")[0] for unit_str in selected_unit_strings
            ]

            units_modified_count = 0

            for nid in selected_unit_nids:
                unit_data = current_unit_info[nid]
                raw_items = unit_data["raw_items"]
                initial_count = len(raw_items)

                if is_droppable_filter:
                    item_to_delete = [item_nid_to_delete, is_droppable_filter]
                    raw_items[:] = [
                        item for item in raw_items if item != item_to_delete
                    ]
                else:
                    raw_items[:] = [
                        item for item in raw_items if item[0] != item_nid_to_delete
                    ]

                if len(raw_items) < initial_count:
                    units_modified_count += 1

            current_chapter_data = chapter_data_map.get(current_chapter_file)
            current_unit_info = get_unit_info(current_chapter_data, selected_unit_nids)
            first_unit_nid = selected_unit_nids[0]
            display_items = current_unit_info.get(first_unit_nid, {}).get("items", [])
            window["-ITEM_LIST-"].update(values=display_items)

            if units_modified_count > 0:
                sg.popup_quick_message(
                    f"Deleted {item_nid_to_delete} from {units_modified_count} unit(s).",
                )
            else:
                sg.popup_quick_message(
                    f"Item {item_nid_to_delete} not found on selected units.",
                )

        elif event == "-SAVE_CHANGES-":
            if not current_chapter_file:
                sg.popup_warning("No chapter selected to save.")
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
            else:
                sg.popup_error(f"Failed to save changes to {current_chapter_file}.")

    window.close()


if __name__ == "__main__":
    main_loop()
