import logging
from bs4 import BeautifulSoup, Tag
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def _get_text_from_output_tag(cell: Tag) -> str:
    output_tag = cell.find("output")
    if output_tag:
        return output_tag.get_text(strip=True)
    return cell.get_text(strip=True)


def extract_marks(html_content: str) -> Dict[str, Dict[str, Any]]:
    course_marks_data: Dict[str, Dict[str, Any]] = {}
    try:
        if not html_content:
            return course_marks_data
        soup = BeautifulSoup(html_content, "html.parser")
        form_element = soup.find("form", id="studentMarkView")
        if not form_element:
            logger.warning("Form with id 'studentMarkView' not found.")
            return course_marks_data
        main_table_container = form_element.find("div", class_="fixedTableContainer")
        if not main_table_container:
            logger.warning(
                "Main table container 'div.fixedTableContainer' not found within the form."
            )
            return course_marks_data
        main_marks_table = main_table_container.find("table", class_="customTable")
        if not main_marks_table:
            logger.warning("Main marks table with class 'customTable' not found.")
            return course_marks_data
        current_course_code = None
        current_course_name = None
        table_rows = main_marks_table.find_all(
            "tr", class_="tableContent", recursive=False
        )
        for row_idx, row in enumerate(table_rows):
            cells = row.find_all("td", recursive=False)
            if len(cells) > 1:
                try:
                    current_course_code = cells[2].get_text(strip=True)
                    current_course_name = cells[3].get_text(strip=True)
                    if current_course_code:
                        course_marks_data[current_course_code] = {
                            "course_name": current_course_name,
                            "assessments": {},
                        }
                except IndexError as e:
                    logger.warning(f"IndexError in course info row: {e}", exc_info=True)
                    current_course_code = None
                    current_course_name = None
                    continue
            elif len(cells) == 1 and cells[0].get("colspan") == "9":
                if not current_course_code:
                    continue
                assessment_table = cells[0].find("table", class_="customTable-level1")
                if not assessment_table:
                    continue
                assessment_rows = assessment_table.find_all(
                    "tr", class_="tableContent-level1"
                )
                for assess_row_idx, assess_row in enumerate(assessment_rows):
                    assess_cells = assess_row.find_all("td")
                    if len(assess_cells) >= 7:
                        try:
                            mark_title = _get_text_from_output_tag(assess_cells[1])
                            max_marks_str = _get_text_from_output_tag(assess_cells[2])
                            max_weightage_str = _get_text_from_output_tag(
                                assess_cells[3]
                            )
                            scored_marks_str = _get_text_from_output_tag(
                                assess_cells[5]
                            )
                            weightage_marks_str = _get_text_from_output_tag(
                                assess_cells[6]
                            )
                            try:
                                max_marks = (
                                    float(max_marks_str) if max_marks_str else None
                                )
                            except ValueError:
                                max_marks = max_marks_str
                            try:
                                max_weightage = (
                                    float(max_weightage_str)
                                    if max_weightage_str
                                    else None
                                )
                            except ValueError:
                                max_weightage = max_weightage_str
                            try:
                                scored_marks = (
                                    float(scored_marks_str)
                                    if scored_marks_str
                                    else None
                                )
                            except ValueError:
                                scored_marks = scored_marks_str
                            try:
                                weightage_marks = (
                                    float(weightage_marks_str)
                                    if weightage_marks_str
                                    else None
                                )
                            except ValueError:
                                weightage_marks = weightage_marks_str
                            if mark_title and current_course_code in course_marks_data:
                                assessment_key = mark_title
                                course_marks_data[current_course_code]["assessments"][
                                    assessment_key
                                ] = {
                                    "max_marks": max_marks,
                                    "max_weightage": max_weightage,
                                    "scored_marks": scored_marks,
                                    "weightage_marks": weightage_marks,
                                }
                        except IndexError as e:
                            logger.warning(
                                f"IndexError in assessment row: {e}", exc_info=True
                            )
                            continue
                        except Exception as e:
                            logger.error(f"Error in assessment row: {e}", exc_info=True)
                            continue
        return course_marks_data
    except Exception as e:
        logger.error(f"Error extracting marks: {e}", exc_info=True)
        return course_marks_data


if __name__ == "__main__":
    # --- Configuration ---
    input_html_file = "html_content/marks.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()
