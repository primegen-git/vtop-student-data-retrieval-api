import logging
from bs4 import BeautifulSoup, Tag
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _find_attendance_table(soup: BeautifulSoup) -> Optional[Tag]:
    try:
        container_div = soup.find("div", id="getStudentDetails")
        if not container_div:
            logger.warning(
                "Attendance container div with id 'getStudentDetails' not found."
            )
            return None
        attendance_table = container_div.find("table", class_="table")
        if not attendance_table:
            logger.warning(
                "Attendance table with class 'table' not found in container."
            )
            return None
        return attendance_table
    except Exception as e:
        logger.error(f"Error finding attendance table: {e}", exc_info=True)
        return None


def _extract_attendance_data_from_table(
    table_element: Optional[Tag],
) -> Dict[str, Dict[str, str]]:
    course_attendance_data: Dict[str, Dict[str, str]] = {}
    try:
        if not table_element:
            return course_attendance_data
        tbody = table_element.find("tbody")
        rows_to_parse = []
        if tbody:
            rows_to_parse = tbody.find_all("tr")
        else:
            all_rows = table_element.find_all("tr")
            if len(all_rows) > 1:
                rows_to_parse = all_rows[1:]
        if not rows_to_parse:
            return course_attendance_data
        for row_idx, row in enumerate(rows_to_parse):
            cells = row.find_all("td")
            if cells and cells[0].get("colspan") == "15":
                continue
            if len(cells) >= 12:
                try:

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
                    if course_code:
                        course_attendance_data[course_code] = {
                            "course_name": course_name,
                            "total_class": total_class,
                            "attended_class": attended_class,
                            "attendence_percentage": attendance_percentage,
                        }
                except IndexError as e:
                    logger.warning(f"IndexError in attendance row: {e}", exc_info=True)
                    continue
                except Exception as e:
                    logger.error(f"Error in attendance row: {e}", exc_info=True)
                    continue
        return course_attendance_data
    except Exception as e:
        logger.error(f"Error extracting attendance data from table: {e}", exc_info=True)
        return course_attendance_data


def extract_attendance(html_content: str) -> Dict[str, Dict[str, str]]:
    try:
        if not html_content:
            return {}
        soup = BeautifulSoup(html_content, "html.parser")
        attendance_table_element = _find_attendance_table(soup)
        if not attendance_table_element:
            return {}
        inner_attendance_data = _extract_attendance_data_from_table(
            attendance_table_element
        )
        return inner_attendance_data
    except Exception as e:
        logger.error(f"Error extracting attendance: {e}", exc_info=True)
        return {}


if __name__ == "__main__":

    input_html_file = "html_content/attendence.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()
