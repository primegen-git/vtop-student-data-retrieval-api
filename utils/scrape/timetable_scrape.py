from bs4 import BeautifulSoup
import json
import re


def extract_timetable_info(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    course_details_map = {}
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
        return timetable_data

    registered_courses_table = student_details_div.find("table", class_="table")
    if not registered_courses_table:
        return timetable_data

    rows = registered_courses_table.find_all("tr")

    for row in rows:
        if row.find("th"):
            continue

        cells = row.find_all("td")
        if len(cells) > 8:
            course_text = cells[2].find("p").get_text(strip=True)
            ltpc_text = cells[3].get_text(strip=True)
            slot_text = cells[7].find_all("p")[0].get_text(strip=True).replace(" -", "")
            venue_text = cells[7].find_all("p")[1].get_text(strip=True)
            faculty_text = cells[8].find("p").get_text(strip=True).replace(" -", "")

            course_code_match = re.match(r"([A-Z0-9]+)", course_text)
            if course_code_match:
                course_code = course_code_match.group(1)
                course_name = (
                    course_text.split(" - ", 1)[1] if " - " in course_text else ""
                )
                credit = ltpc_text.split()[-1]

                course_details_map[course_code] = {
                    "course_name": course_name,
                    "credit": credit,
                    "faculty-name": faculty_text,
                    "slot": slot_text,
                    "venue": venue_text,
                }

    timetable_grid = soup.find("table", id="timeTableStyle")
    if not timetable_grid:
        return timetable_data

    day_map_short_to_long = {
        "mon": "monday",
        "tue": "tuesday",
        "wed": "wednesday",
        "thu": "thursday",
        "fri": "friday",
        "sat": "saturday",
        "sun": "sunday",
    }

    day_indicator_cells = timetable_grid.find_all("td", rowspan="2", bgcolor="#e2e2e2")

    for day_cell in day_indicator_cells:
        short_day = day_cell.get_text(strip=True).lower()

        if short_day not in day_map_short_to_long:
            continue

        current_day_key = day_map_short_to_long[short_day]

        theory_row = day_cell.find_parent("tr")
        lab_row = theory_row.find_next_sibling("tr")

        if not theory_row or not lab_row:
            continue

        all_rows = [theory_row, lab_row]
        for current_row in all_rows:
            for slot_td in current_row.find_all("td"):
                if slot_td.get("bgcolor", "").upper() == "#FC6C85":
                    slot_text = slot_td.get_text(strip=True)
                    if not slot_text or slot_text == "-":
                        continue

                    parts = slot_text.split("-")
                    if len(parts) > 1:
                        slot_info = parts[0]
                        course_code = parts[1]
                        details_from_map = course_details_map.get(course_code, {})

                        entry = {
                            "course_name": details_from_map.get(
                                "course_name", "Unknown Course"
                            ),
                            "course_code": course_code,
                            "details": {
                                "credit": details_from_map.get("credit", ""),
                                "faculty-name": details_from_map.get(
                                    "faculty-name", ""
                                ),
                                "slot": details_from_map.get("slot", ""),
                                "venue": details_from_map.get("venue", ""),
                            },
                        }
                        timetable_data[current_day_key].append(entry)

    return timetable_data


if __name__ == "__main__":
    html_file_path = "html_content/timetable.html"
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_file_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: '{html_file_path}' not found.")
        exit()

    extracted_information = extract_timetable_info(html_file_content)

    print("\n--- Final Extracted Timetable ---")
    print(json.dumps(extracted_information, indent=4))
