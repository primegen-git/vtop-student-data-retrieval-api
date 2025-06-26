import logging
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)


def extract_timetable(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        course_code_to_name = {}
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
            logger.error(
                "'studentDetailsList' div not found. Cannot get course code to name mapping."
            )
        else:
            registered_courses_table_div = student_details_div.find(
                "div", class_="table-responsive"
            )
            if not registered_courses_table_div:
                logger.error("Registered courses table's responsive div not found.")
            else:
                registered_courses_table = registered_courses_table_div.find(
                    "table", class_="table"
                )
                if not registered_courses_table:
                    logger.error("Registered courses table (class='table') not found.")
                else:
                    rows = registered_courses_table.find_all("tr")
                    for i, row in enumerate(rows):
                        header_cells = row.find_all("th")
                        if header_cells:
                            continue
                        cells = row.find_all("td")
                        if len(cells) > 2:
                            course_info_cell = cells[2]
                            p_tags_in_course_cell = course_info_cell.find_all("p")
                            if p_tags_in_course_cell:
                                course_full_string = ""
                                if len(
                                    p_tags_in_course_cell
                                ) > 1 and " - " not in p_tags_in_course_cell[
                                    0
                                ].get_text(
                                    strip=True
                                ):
                                    potential_code = p_tags_in_course_cell[0].get_text(
                                        strip=True
                                    )
                                    potential_name = p_tags_in_course_cell[1].get_text(
                                        strip=True
                                    )
                                    if re.match(
                                        r"^[A-Z0-9]+[A-Z0-9MPL]*$", potential_code
                                    ):
                                        course_full_string = (
                                            f"{potential_code} - {potential_name}"
                                        )
                                    else:
                                        course_full_string = p_tags_in_course_cell[
                                            0
                                        ].get_text(strip=True)
                                elif p_tags_in_course_cell[0]:
                                    course_full_string = p_tags_in_course_cell[
                                        0
                                    ].get_text(strip=True)
                                parts = course_full_string.split(" - ", 1)
                                if len(parts) == 2:
                                    course_code = parts[0].strip()
                                    course_name = parts[1].strip()
                                    if course_code:
                                        course_code_to_name[course_code] = course_name
                                elif (
                                    cells[1]
                                    and "MOOC" in cells[1].get_text(strip=True)
                                    and course_full_string
                                ):
                                    match = re.match(
                                        r"([A-Z0-9]+[A-Z0-9MPL]+)\s+(.*)",
                                        course_full_string,
                                    )
                                    if match:
                                        course_code = match.group(1).strip()
                                        course_name = match.group(2).strip()
                                        if course_code:
                                            course_code_to_name[course_code] = (
                                                course_name
                                            )
        if not course_code_to_name:
            logger.warning(
                "Course code to name map is empty. Timetable names might be 'Unknown Course'."
            )
        timetable_grid = soup.find("table", id="timeTableStyle")
        if not timetable_grid:
            logger.error("Timetable grid (table#timeTableStyle) not found.")
            return timetable_data
        day_indicator_cells = timetable_grid.find_all(
            "td", attrs={"rowspan": "2", "bgcolor": "#e2e2e2"}
        )
        if not day_indicator_cells:
            logger.warning(
                "Could not find day indicator cells with rowspan=2 and bgcolor=#e2e2e2. Trying fallback."
            )
            all_rowspan2_tds = timetable_grid.find_all("td", rowspan="2")
            day_indicator_cells = []
            for cell in all_rowspan2_tds:
                cell_text = cell.get_text(strip=True).upper()
                if cell_text in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                    bgcolor = cell.get("bgcolor", "").lower()
                    if (
                        "e2e2e2" in bgcolor
                        or "dcdcdc" in bgcolor
                        or "c0c0c0" in bgcolor
                        or not bgcolor
                    ):
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
                logger.warning(
                    f"Unknown or unmappable day key '{extracted_short_day}'. Skipping."
                )
                continue
            theory_row = indicator_cell.find_parent("tr")
            if not theory_row:
                logger.warning(
                    f"Could not find parent <tr> for theory_row for {current_day_key}. Skipping."
                )
                continue
            lab_row = theory_row.find_next_sibling("tr")
            days_processed_count += 1
            theory_slot_cells = theory_row.find_all("td")
            theory_start_index = 0
            if theory_slot_cells:
                if theory_slot_cells[0] == indicator_cell:
                    if (
                        len(theory_slot_cells) > 1
                        and theory_slot_cells[1].get_text(strip=True).upper()
                        == "THEORY"
                    ):
                        theory_start_index = 2
                    else:
                        theory_start_index = 1
                elif theory_slot_cells[0].get_text(strip=True).upper() == "THEORY":
                    theory_start_index = 1
            for cell_idx, slot_td in enumerate(theory_slot_cells):
                if cell_idx < theory_start_index:
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
            if lab_row:
                lab_slot_cells = lab_row.find_all("td")
                lab_start_index = 0
                if (
                    lab_slot_cells
                    and lab_slot_cells[0].get_text(strip=True).upper() == "LAB"
                ):
                    lab_start_index = 1
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
                            details = (
                                "-".join(parts[2:]).strip() if len(parts) > 2 else ""
                            )
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
        return timetable_data
    except Exception as e:
        logger.error(f"Error extracting timetable: {e}", exc_info=True)
        return {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": [],
        }


if __name__ == "__main__":
    html_file_path = "html_content/timetable.html"  # Make sure this path is correct
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(extract_timetable(html_content))
