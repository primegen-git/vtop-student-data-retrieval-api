import logging
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


def extract_grade_history(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        grades_data = {}
        effective_grades_header_td = soup.find(
            lambda tag: tag.name == "td"
            and tag.get("colspan") == "11"
            and "Effective Grades" in tag.get_text(strip=True)
        )
        if not effective_grades_header_td:
            logger.warning("Effective Grades header not found in HTML.")
            return grades_data
        grades_table = effective_grades_header_td.find_parent("table")
        if not grades_table:
            logger.warning("Grades table not found for Effective Grades header.")
            return grades_data
        course_rows = grades_table.find_all("tr", class_="tableContent")
        for row in course_rows:
            if row.get("id") and row["id"].startswith("detailsView_"):
                continue
            cells = row.find_all("td")
            if len(cells) >= 8:
                try:
                    course_code = cells[1].get_text(strip=True)
                    course_name = cells[2].get_text(strip=True)
                    course_type = cells[3].get_text(strip=True)
                    credits = cells[4].get_text(strip=True)
                    grade = cells[5].get_text(strip=True)
                    exam_month = cells[6].get_text(strip=True)
                    result_declared = cells[7].get_text(strip=True)
                    if not course_code:
                        continue
                    grades_data[course_code] = {
                        "couse_name": course_name,
                        "course_type": course_type,
                        "credit": credits,
                        "grade": grade,
                        "exam_month": exam_month,
                        "result_decalred": result_declared,
                    }
                except IndexError as e:
                    logger.warning(
                        f"Skipping row due to unexpected cell count or structure: {e}",
                        exc_info=True,
                    )
                    continue
        return grades_data
    except Exception as e:
        logger.error(f"Error extracting grade history: {e}", exc_info=True)
        return {}


if __name__ == "__main__":
    # This part is for testing. When used as a module, this won't run.
    try:
        with open("html_content/grade_history.html", "r", encoding="utf-8") as f:
            html_file_content = f.read()
    except FileNotFoundError:
        print(
            "Error: 'grade_history.html' not found. Please ensure the file is in the same directory."
        )
        exit()

    extracted_information = extract_grade_history(html_file_content)

    # Print the extracted information in JSON format
