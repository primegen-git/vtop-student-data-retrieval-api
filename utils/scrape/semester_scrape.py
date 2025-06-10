from bs4 import BeautifulSoup
from typing import Dict


# --- Main importable function ---
def extract_semester(html_content: str) -> Dict[str, str]:
    """
    Extracts semester information from an HTML content string.

    This function parses the HTML content to find a select dropdown
    with id 'semesterSubId' and extracts the semester codes (value attribute)
    and semester names (text content) from its options.

    Args:
        html_content: The HTML content as a string.

    Returns:
        A dictionary where keys are semester codes and values are semester names.
        Returns an empty dictionary if the select element is not found or
        no valid options are present.
    """
    semester_data: Dict[str, str] = {}
    if not html_content:
        print("Error: HTML content is empty.")
        return semester_data

    soup = BeautifulSoup(html_content, "html.parser")

    # Find the select element by its ID
    select_element = soup.find("select", id="semesterSubId")

    if not select_element:
        print("Error: Could not find the select element with id 'semesterSubId'.")
        return semester_data

    # Find all option tags within the select element
    option_tags = select_element.find_all("option")

    if not option_tags:
        print("No option tags found within the select element.")
        return semester_data

    for option in option_tags:
        semester_code = option.get("value")
        semester_name = option.get_text(strip=True)

        # Ensure the semester_code is not empty (to skip placeholder like "--Choose Semester--")
        # and the name is also not just a placeholder text if code is empty.
        if semester_code:  # We only care about options with a value
            semester_data[semester_code] = semester_name
        # elif semester_name and "--Choose Semester--" not in semester_name:
        # Optionally handle cases where a value might be missing but text is present
        # For this problem, we only care about options with a value.
        # print(f"Skipping option with no value: {semester_name}")

    return semester_data


if __name__ == "__main__":
    # --- Configuration ---
    # This part runs only when the script is executed directly.

    input_html_file = "html_content/semester.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    print(extract_semester(html_content))
