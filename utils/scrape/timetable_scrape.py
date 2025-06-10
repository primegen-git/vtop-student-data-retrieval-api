from bs4 import BeautifulSoup
import json
import re


def extract_timetable(html_content):
    """
    Extracts timetable information from HTML content.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    course_code_to_name = {}
    # Initialize with full day names for the desired output
    timetable_data = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": [],
    }

    student_details_div = soup.find("div", id="studentDetailsList")
    if not student_details_div:
        print(
            "ERROR: 'studentDetailsList' div not found. Cannot get course code to name mapping."
        )
        # return timetable_data # Keep trying to parse timetable even if names are unknown
    else:
        registered_courses_table_div = student_details_div.find(
            "div", class_="table-responsive"
        )
        if not registered_courses_table_div:
            print("ERROR: Registered courses table's responsive div not found.")
        else:
            registered_courses_table = registered_courses_table_div.find(
                "table", class_="table"
            )
            if not registered_courses_table:
                print("ERROR: Registered courses table (class='table') not found.")
            else:
                rows = registered_courses_table.find_all("tr")

                for i, row in enumerate(rows):
                    header_cells = row.find_all("th")
                    if header_cells:
                        # print(f"Row {i}: Skipping header row.")
                        continue

                    cells = row.find_all("td")
                    # Expecting: Sl.No | Category | Course (Code - Title) | ...
                    if len(cells) > 2:  # Need at least up to the course cell
                        # The course code and title are usually in the 3rd cell (index 2)
                        # within <p> tags.
                        course_info_cell = cells[2]
                        p_tags_in_course_cell = course_info_cell.find_all("p")

                        if p_tags_in_course_cell:
                            course_full_string = ""
                            # Sometimes the code and name are in separate <p> tags, or combined
                            if len(
                                p_tags_in_course_cell
                            ) > 1 and " - " not in p_tags_in_course_cell[0].get_text(
                                strip=True
                            ):
                                # Attempt to combine if they look like separate code and name
                                # This is a heuristic and might need adjustment based on actual HTML
                                potential_code = p_tags_in_course_cell[0].get_text(
                                    strip=True
                                )
                                potential_name = p_tags_in_course_cell[1].get_text(
                                    strip=True
                                )
                                if re.match(
                                    r"^[A-Z0-9]+[A-Z0-9MPL]*$", potential_code
                                ):  # Basic check for course code format
                                    course_full_string = (
                                        f"{potential_code} - {potential_name}"
                                    )
                                else:  # Fallback to first p tag if combination doesn't make sense
                                    course_full_string = p_tags_in_course_cell[
                                        0
                                    ].get_text(strip=True)
                            elif p_tags_in_course_cell[0]:
                                course_full_string = p_tags_in_course_cell[0].get_text(
                                    strip=True
                                )

                            parts = course_full_string.split(" - ", 1)
                            if len(parts) == 2:
                                course_code = parts[0].strip()
                                course_name = parts[1].strip()
                                if course_code:  # Ensure course_code is not empty
                                    course_code_to_name[course_code] = course_name
                                    # print(f"  Mapped: {course_code} -> {course_name}")
                            # Fallback for MOOC or other formats if the primary split fails
                            elif (
                                cells[1]
                                and "MOOC" in cells[1].get_text(strip=True)
                                and course_full_string
                            ):
                                # Regex for MOOC: CODE followed by Name
                                match = re.match(
                                    r"([A-Z0-9]+[A-Z0-9MPL]+)\s+(.*)",
                                    course_full_string,
                                )
                                if match:
                                    course_code = match.group(1).strip()
                                    course_name = match.group(2).strip()
                                    if course_code:
                                        course_code_to_name[course_code] = course_name
                                        # print(f"  Mapped MOOC: {course_code} -> {course_name}")
                                # else:
                                # print(f"  Warning: Could not parse MOOC string: '{course_full_string}'")
                            # else:
                            # print(f"  Warning: Could not parse course string: '{course_full_string}'")
                        # else:
                        # print(f"  Row {i}, Col 2: No <p> tags found in course cell.")
                    elif (
                        len(cells) > 0
                        and "Total Number Of Credits" in cells[0].get_text()
                    ):
                        # print(f"Row {i}: Skipping total credits row.")
                        pass  # This is the "Total Number Of Credits" row
                    # else:
                    # print(f"  Row {i}: Not enough cells for course info or not a relevant row. Cells: {len(cells)}")

    print(f"Finished Step 1. Course Code to Name Map: {course_code_to_name}")
    if not course_code_to_name:
        print(
            "WARNING: Course code to name map is empty. Timetable names might be 'Unknown Course'."
        )

    # --- Step 2: Parse the Timetable Grid ---
    timetable_grid = soup.find("table", id="timeTableStyle")
    if not timetable_grid:
        print("ERROR: Timetable grid (table#timeTableStyle) not found.")
        return timetable_data

    # Find all <td> elements that typically indicate the day
    # These usually have rowspan="2" and a specific bgcolor or known text content.
    # VTOP often uses bgcolor="#e2e2e2" for these day indicator cells.
    day_indicator_cells = timetable_grid.find_all(
        "td", attrs={"rowspan": "2", "bgcolor": "#e2e2e2"}
    )

    # Fallback if bgcolor is not reliable or slightly different (e.g. case)
    if not day_indicator_cells:
        print(
            "Warning: Could not find day indicator cells with rowspan=2 and bgcolor=#e2e2e2. Trying rowspan=2 and checking text."
        )
        all_rowspan2_tds = timetable_grid.find_all("td", rowspan="2")
        day_indicator_cells = []
        for cell in all_rowspan2_tds:
            cell_text = cell.get_text(strip=True).upper()
            if cell_text in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                # Check if the bgcolor is somewhat greyish as an additional heuristic
                bgcolor = cell.get("bgcolor", "").lower()
                if (
                    "e2e2e2" in bgcolor
                    or "dcdcdc" in bgcolor
                    or "c0c0c0" in bgcolor
                    or not bgcolor
                ):  # Accept common grey or no bgcolor
                    day_indicator_cells.append(cell)

    day_map_short_to_long = {
        "mon": "monday",
        "tue": "tuesday",
        "wed": "wednesday",
        "thu": "thursday",
        "fri": "friday",
        "sat": "saturday",
        "sun": "sunday",
    }

    days_processed_count = 0
    for indicator_cell in day_indicator_cells:
        extracted_short_day = indicator_cell.get_text(strip=True).lower()
        current_day_key = day_map_short_to_long.get(extracted_short_day)

        if not current_day_key or current_day_key not in timetable_data:
            print(
                f"    Warning: Unknown or unmappable day key '{extracted_short_day}'. Skipping."
            )
            continue

        theory_row = indicator_cell.find_parent("tr")
        if not theory_row:
            print(
                f"    Warning: Could not find parent <tr> for theory_row for {current_day_key}. Skipping."
            )
            continue

        lab_row = theory_row.find_next_sibling("tr")
        # lab_row can be None if it's the last day and only has a theory row, or if HTML is malformed.
        # We will check `if lab_row:` before processing it.

        days_processed_count += 1

        # Process Theory Slots
        theory_slot_cells = theory_row.find_all("td")
        theory_start_index = 0
        if theory_slot_cells:
            if theory_slot_cells[0] == indicator_cell:  # Day cell is the first
                if (
                    len(theory_slot_cells) > 1
                    and theory_slot_cells[1].get_text(strip=True).upper() == "THEORY"
                ):
                    theory_start_index = 2
                else:
                    theory_start_index = 1
                    # print(f"    Note: Theory row for {current_day_key} starts with day, but no explicit 'THEORY' label next to it.")
            elif theory_slot_cells[0].get_text(strip=True).upper() == "THEORY":
                theory_start_index = 1
            # else:
            # print(f"    Warning: Theory row for {current_day_key} has unexpected start: '{theory_slot_cells[0].get_text(strip=True)}'")

        for cell_idx, slot_td in enumerate(theory_slot_cells):
            if cell_idx < theory_start_index:
                continue

            slot_bgcolor = slot_td.get(
                "bgcolor", ""
            ).lower()  # Default to empty string and lower case
            if slot_bgcolor == "#ccff33":  # Check the specific color for active slots
                p_tag = slot_td.find("p")
                slot_text = (
                    p_tag.get_text(strip=True)
                    if p_tag
                    else slot_td.get_text(strip=True)
                )

                if not slot_text or slot_text == "-":
                    continue

                parts = slot_text.split("-")
                if len(parts) >= 2:
                    slot_info = parts[0].strip()
                    course_code_from_slot = parts[1].strip()
                    details = (
                        "-".join(parts[2:]).strip() if len(parts) > 2 else ""
                    )  # Join remaining parts for details

                    course_name_from_map = course_code_to_name.get(
                        course_code_from_slot,
                        f"Unknown Course ({course_code_from_slot})",  # Fallback name
                    )

                    entry = {
                        "slot_info": slot_info,
                        "course_name": course_name_from_map,
                        "course_code": course_code_from_slot,
                        "details": details,
                    }
                    if entry not in timetable_data[current_day_key]:
                        timetable_data[current_day_key].append(entry)
                        # print(f"    Added THEORY: {entry} to {current_day_key}")
                # else:
                # print(f"    Skipping THEORY slot with unparseable text: '{slot_text}' in {current_day_key}")

        # Process Lab Slots (only if lab_row exists)
        if lab_row:
            lab_slot_cells = lab_row.find_all("td")
            lab_start_index = 0
            if (
                lab_slot_cells
                and lab_slot_cells[0].get_text(strip=True).upper() == "LAB"
            ):
                lab_start_index = 1
            # else:
            # If the first cell isn't "LAB", it might be an empty cell or directly slots.
            # print(f"    Note: Lab row for {current_day_key} does not start with 'LAB' label (or no lab cells). First cell: '{lab_slot_cells[0].get_text(strip=True) if lab_slot_cells else 'None'}'")

            for cell_idx, slot_td in enumerate(lab_slot_cells):
                if cell_idx < lab_start_index:
                    continue

                slot_bgcolor = slot_td.get("bgcolor", "").lower()
                if slot_bgcolor == "#ccff33":
                    p_tag = slot_td.find("p")
                    slot_text = (
                        p_tag.get_text(strip=True)
                        if p_tag
                        else slot_td.get_text(strip=True)
                    )

                    if not slot_text or slot_text == "-":
                        continue

                    parts = slot_text.split("-")
                    if len(parts) >= 2:
                        slot_info = parts[0].strip()
                        course_code_from_slot = parts[1].strip()
                        details = "-".join(parts[2:]).strip() if len(parts) > 2 else ""

                        course_name_from_map = course_code_to_name.get(
                            course_code_from_slot,
                            f"Unknown Course ({course_code_from_slot})",
                        )

                        entry = {
                            "slot_info": slot_info,
                            "course_name": course_name_from_map,
                            "course_code": course_code_from_slot,
                            "details": details,
                        }
                        if entry not in timetable_data[current_day_key]:
                            timetable_data[current_day_key].append(entry)
                            # print(f"    Added LAB: {entry} to {current_day_key}")
                    # else:
                    # print(f"    Skipping LAB slot with unparseable text: '{slot_text}' in {current_day_key}")
        # else:
        # print(f"    No lab row found or processed for {current_day_key}.")

    print(f"Finished processing {days_processed_count} actual days from indicators.")
    return timetable_data


if __name__ == "__main__":
    html_file_path = "html_content/timetable.html"  # Make sure this path is correct
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(extract_timetable(html_content))
