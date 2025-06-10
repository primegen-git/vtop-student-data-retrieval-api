import aiofiles
from bs4 import BeautifulSoup, Tag
import json
from typing import Dict, Optional


# --- Internal helper functions for parsing ---
def _find_attendance_table(soup: BeautifulSoup) -> Optional[Tag]:
    """
    Finds the main attendance table within the parsed HTML. (Internal use)
    """
    container_div = soup.find("div", id="getStudentDetails")
    if not container_div:
        print("DEBUG: Could not find the container div with id 'getStudentDetails'.")
        return None

    attendance_table = container_div.find("table", class_="table")
    if not attendance_table:
        print("DEBUG: Could not find the attendance table with class 'table'.")
        return None

    return attendance_table


def _extract_attendance_data_from_table(
    table_element: Optional[Tag],
) -> Dict[str, Dict[str, str]]:
    """
    Extracts attendance information from the attendance table Tag. (Internal use)
    This directly returns the dictionary of courses as requested for the "inner part".
    """
    course_attendance_data: Dict[str, Dict[str, str]] = {}
    if not table_element:
        return course_attendance_data

    # The table has a <thead>, so find_all('tr') on the table itself
    # will include the header row. We need to skip it.
    # Alternatively, find <tbody> first if it exists, or just slice rows.

    tbody = table_element.find("tbody")  # VTOP tables often have explicit tbody
    rows_to_parse = []
    if tbody:
        rows_to_parse = tbody.find_all("tr")
    else:
        # Fallback if no tbody, skip the first row (header)
        all_rows = table_element.find_all("tr")
        if len(all_rows) > 1:
            rows_to_parse = all_rows[1:]

    if not rows_to_parse:
        print("DEBUG: No data rows found in the table body.")
        return course_attendance_data

    for row_idx, row in enumerate(rows_to_parse):
        cells = row.find_all("td")

        # Check for the summary row at the end (colspan="15")
        if cells and cells[0].get("colspan") == "15":
            # print(f"DEBUG: Skipping summary row at row index {row_idx}.")
            continue

        # Expected columns for attendance data:
        # Index 1: Course Code
        # Index 2: Course Title
        # Index 9: Attended Classes
        # Index 10: Total Classes
        # Index 11: Attendance Percentage
        if len(cells) >= 12:  # Need at least up to 'Attendance Percentage'
            try:
                # Helper to get text, prioritizing <p> tag
                def get_cell_text(cell_tag: Tag) -> str:
                    p_tag = cell_tag.find("p")
                    if p_tag:
                        return p_tag.get_text(strip=True)
                    return cell_tag.get_text(strip=True)

                course_code = get_cell_text(cells[1])
                course_name = get_cell_text(cells[2])
                attended_class = get_cell_text(cells[9])
                total_class = get_cell_text(cells[10])
                attendance_percentage = get_cell_text(cells[11])

                # Ensure course_code is not empty, as it's the key
                if course_code:
                    course_attendance_data[course_code] = {
                        "course_name": course_name,
                        "total_class": total_class,
                        "attended_class": attended_class,
                        "attendence_percentage": attendance_percentage,  # Typo as per requirement
                    }
                # else:
                # print(f"DEBUG: Row {row_idx} - Empty course code found.")

            except IndexError:
                # print(f"DEBUG: Row {row_idx} - IndexError (not enough cells or issue with cell access). Cell count: {len(cells)}")
                continue
            except Exception as e:
                # print(f"DEBUG: Row {row_idx} - An error occurred: {e}")
                continue
        # else:
        # print(f"DEBUG: Row {row_idx} - Skipped, not enough cells: {len(cells)} found.")

    return course_attendance_data


# --- Main importable function ---
def extract_attendance(html_content: str) -> Dict[str, Dict[str, str]]:
    """
    Extracts course attendance details from an HTML content string,
    returning the inner dictionary structure {course_code: details}.

    Args:
        html_content: The HTML content as a string.

    Returns:
        A dictionary containing the extracted course attendance data,
        structured as {course_code: {details...}}.
        Returns an empty dictionary if critical elements are not found or no data is extracted.
    """
    if not html_content:
        print("Error: HTML content is empty.")
        return {}

    soup = BeautifulSoup(html_content, "html.parser")

    attendance_table_element = _find_attendance_table(soup)
    if not attendance_table_element:
        # Error message printed in _find_attendance_table
        return {}

    # This function directly returns the structure you need for the "inner part"
    inner_attendance_data = _extract_attendance_data_from_table(
        attendance_table_element
    )

    return inner_attendance_data


if __name__ == "__main__":

    input_html_file = "html_content/attendence.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    print(extract_attendance(html_content))
