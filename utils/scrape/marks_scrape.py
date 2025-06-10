from bs4 import BeautifulSoup, Tag
import json
from typing import Dict, List, Optional, Any


def _get_text_from_output_tag(cell: Tag) -> str:
    """Helper to get text from an <output> tag within a cell, or cell's direct text."""
    output_tag = cell.find("output")
    if output_tag:
        return output_tag.get_text(strip=True)
    return cell.get_text(strip=True)


# --- Main importable function ---
def extract_marks(html_content: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts marks details for courses from an HTML content string.
    This returns the inner structure {course_code: {course_name: "...", "assessments": {assessment_title: details...}}}.
    The "assessments" key replaces "mark_title" for clarity and to hold multiple assessments.

    Args:
        html_content: The HTML content as a string.

    Returns:
        A dictionary containing the extracted marks data for courses.
        Returns an empty dictionary if critical elements are not found or no data is extracted.
    """
    course_marks_data: Dict[str, Dict[str, Any]] = {}
    if not html_content:
        print("DEBUG: HTML content is empty.")
        return course_marks_data

    soup = BeautifulSoup(html_content, "html.parser")

    # Find the main container for the marks table (it doesn't have a specific ID for the table itself)
    # The table is within a div with class "fixedTableContainer"
    # and is a direct child of div with id "fixedTableContainer"

    # The courses and their marks are in a table with class "customTable"
    # This table is inside a div with class "fixedTableContainer"
    # We need to find the correct "fixedTableContainer" that holds the marks.
    # The one directly under form#studentMarkView seems most relevant.

    form_element = soup.find("form", id="studentMarkView")
    if not form_element:
        print("DEBUG: Form with id 'studentMarkView' not found.")
        return course_marks_data

    # The marks table is usually within a div with class 'fixedTableContainer' inside the form
    # Let's find all such containers and pick the one that looks like a marks table.
    # The actual marks table structure is:
    # <tr> (course details)
    # <tr> (nested table with assessments)

    # The primary table holding courses and then nested assessment tables
    # is usually a 'customTable' within 'fixedTableContainer'.
    # We'll iterate through all 'tableContent' rows of the main 'customTable'.

    main_table_container = form_element.find("div", class_="fixedTableContainer")
    if not main_table_container:
        print(
            "DEBUG: Main table container 'div.fixedTableContainer' not found within the form."
        )
        return course_marks_data

    main_marks_table = main_table_container.find("table", class_="customTable")
    if not main_marks_table:
        print("DEBUG: Main marks table 'table.customTable' not found.")
        return course_marks_data

    # Iterate through rows in the main table.
    # Rows with course info and rows with nested assessment tables both have class 'tableContent'.
    current_course_code = None
    current_course_name = None

    table_rows = main_marks_table.find_all("tr", class_="tableContent", recursive=False)
    # print(f"DEBUG: Found {len(table_rows)} 'tr.tableContent' rows in main marks table.")

    for row_idx, row in enumerate(table_rows):
        cells = row.find_all("td", recursive=False)

        # Check if this row contains course details (usually more than 1 cell)
        # or a nested table (usually 1 cell with colspan)
        if len(cells) > 1:  # This is likely a course information row
            try:
                # Sl.No. [0], ClassNbr [1], Course Code [2], Course Title [3], ...
                current_course_code = cells[2].get_text(strip=True)
                current_course_name = cells[3].get_text(strip=True)
                # print(f"DEBUG: Processing course: {current_course_code} - {current_course_name}")
                if current_course_code:
                    course_marks_data[current_course_code] = {
                        "course_name": current_course_name,
                        "assessments": {},  # Changed "mark_title" to "assessments"
                    }
            except IndexError:
                # print(f"DEBUG: IndexError processing course info row {row_idx}. Cells: {len(cells)}")
                current_course_code = None  # Reset if error
                current_course_name = None
                continue

        elif (
            len(cells) == 1 and cells[0].get("colspan") == "9"
        ):  # This is a row with a nested assessment table
            if not current_course_code:
                # print("DEBUG: Found assessment table row but no current course context. Skipping.")
                continue

            assessment_table = cells[0].find("table", class_="customTable-level1")
            if not assessment_table:
                # print(f"DEBUG: Nested assessment table 'customTable-level1' not found for {current_course_code}.")
                continue

            assessment_rows = assessment_table.find_all(
                "tr", class_="tableContent-level1"
            )
            # print(f"DEBUG: Found {len(assessment_rows)} assessment rows for {current_course_code}.")

            for assess_row_idx, assess_row in enumerate(assessment_rows):
                assess_cells = assess_row.find_all("td")
                if len(assess_cells) >= 7:  # Need at least up to Weightage Mark
                    try:
                        # Sl.No.[0], Mark Title[1], Max. Mark[2], Weightage %[3], Status[4], Scored Mark[5], Weightage Mark[6]
                        mark_title = _get_text_from_output_tag(assess_cells[1])
                        max_marks_str = _get_text_from_output_tag(assess_cells[2])
                        max_weightage_str = _get_text_from_output_tag(assess_cells[3])
                        # status = _get_text_from_output_tag(assess_cells[4]) # Not in desired output
                        scored_marks_str = _get_text_from_output_tag(assess_cells[5])
                        weightage_marks_str = _get_text_from_output_tag(assess_cells[6])

                        # Attempt to convert to float/int, handle empty strings or non-numeric
                        try:
                            max_marks = float(max_marks_str) if max_marks_str else None
                        except ValueError:
                            max_marks = max_marks_str  # Keep as string if not floatable
                        try:
                            max_weightage = (
                                float(max_weightage_str) if max_weightage_str else None
                            )
                        except ValueError:
                            max_weightage = max_weightage_str
                        try:
                            scored_marks = (
                                float(scored_marks_str) if scored_marks_str else None
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
                            # Use a more descriptive key for each assessment type if needed,
                            # or just use the mark_title directly.
                            # For simplicity, using mark_title. If titles can repeat, a counter or
                            # more unique key generation would be needed.
                            assessment_key = (
                                mark_title  # Or sanitize this key if needed
                            )

                            course_marks_data[current_course_code]["assessments"][
                                assessment_key
                            ] = {
                                "max_marks": max_marks,
                                "max_weightage": max_weightage,
                                "scored_marks": scored_marks,
                                "weightage_marks": weightage_marks,
                            }
                        # else:
                        # print(f"DEBUG: Missing mark_title or course_code not in dict for assessment row {assess_row_idx} of {current_course_code}")

                    except IndexError:
                        # print(f"DEBUG: IndexError processing assessment row {assess_row_idx} for {current_course_code}. Cells: {len(assess_cells)}")
                        continue
                    except Exception as e:
                        # print(f"DEBUG: Error processing assessment row {assess_row_idx} for {current_course_code}: {e}")
                        continue
            # Reset current_course_code after processing its assessments to handle next course block
            # current_course_code = None # This might be too soon if multiple assessment tables per course, unlikely
            # current_course_name = None

    return course_marks_data


if __name__ == "__main__":
    # --- Configuration ---
    input_html_file = "html_content/marks.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    print(extract_marks(html_content))
