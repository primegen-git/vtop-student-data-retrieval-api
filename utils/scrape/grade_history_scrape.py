from bs4 import BeautifulSoup
import json


def extract_grade_history(html_content):
    """
    Extracts course grade information from HTML content.

    Args:
        html_content (str): The HTML content as a string.

    Returns:
        dict: A dictionary where keys are course codes and values are
              dictionaries containing course details.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    grades_data = {}

    # Find the table containing "Effective Grades"
    # We can identify it by the specific header row text
    effective_grades_header_td = soup.find(
        lambda tag: tag.name == "td"
        and tag.get("colspan") == "11"
        and "Effective Grades" in tag.get_text(strip=True)
    )

    if not effective_grades_header_td:
        print("Warning: 'Effective Grades' header cell not found.")
        return grades_data

    grades_table = effective_grades_header_td.find_parent("table")

    if not grades_table:
        print("Warning: 'Effective Grades' table not found.")
        return grades_data

    # Get all rows with class 'tableContent' within this specific table
    # These are the rows containing individual course data
    course_rows = grades_table.find_all("tr", class_="tableContent")

    for row in course_rows:
        # Skip rows that are hidden detail views for composite courses
        # These rows also have 'tableContent' but have an 'id' like 'detailsView_COURSECODE'
        if row.get("id") and row["id"].startswith("detailsView_"):
            continue

        cells = row.find_all("td")

        # Ensure the row has enough cells for the data we need
        # Sl.No.[0], Course Code[1], Course Title[2], Course Type[3], Credits[4], Grade[5], Exam Month[6], Result Declared[7]
        if len(cells) >= 8:
            try:
                course_code = cells[1].get_text(strip=True)
                course_name = cells[2].get_text(strip=True)
                course_type = cells[3].get_text(strip=True)
                credits = cells[4].get_text(strip=True)
                grade = cells[5].get_text(strip=True)
                exam_month = cells[6].get_text(strip=True)
                result_declared = cells[7].get_text(strip=True)

                # If course_code is empty, it's likely not a valid course entry row (e.g., a sub-header or malformed row)
                if not course_code:
                    continue

                # Store data using the exact key names from the requested format
                grades_data[course_code] = {
                    "couse_name": course_name,  # Typo "couse_name" as per request
                    "course_type": course_type,
                    "credit": credits,
                    "grade": grade,
                    "exam_month": exam_month,
                    "result_decalred": result_declared,  # Typo "result_decalred" as per request
                }
            except IndexError:
                # This might happen if a 'tableContent' row doesn't have the expected structure
                print(
                    f"Warning: Skipping row due to unexpected cell count or structure: {row}"
                )
                continue
        # else:
        # print(f"Skipping row, not enough cells: {len(cells)}")

    return grades_data


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
    print(json.dumps(extracted_information, indent=4))
