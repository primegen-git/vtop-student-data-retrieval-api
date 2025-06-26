import logging
from bs4 import BeautifulSoup
from typing import Dict

logger = logging.getLogger(__name__)


def extract_semester(html_content: str) -> Dict[str, str]:
    semester_data: Dict[str, str] = {}
    try:
        if not html_content:
            logger.error("HTML content is empty.")
            return semester_data
        soup = BeautifulSoup(html_content, "html.parser")
        select_element = soup.find("select", id="semesterSubId")
        if not select_element:
            logger.error("Could not find the select element with id 'semesterSubId'.")
            return semester_data
        option_tags = select_element.find_all("option")
        if not option_tags:
            logger.warning("No option tags found within the select element.")
            return semester_data
        for option in option_tags:
            semester_code = option.get("value")
            semester_name = option.get_text(strip=True)
            if semester_code:
                semester_data[semester_code] = semester_name
        return semester_data
    except Exception as e:
        logger.error(f"Error extracting semester: {e}", exc_info=True)
        return semester_data


if __name__ == "__main__":
    # --- Configuration ---
    # This part runs only when the script is executed directly.

    input_html_file = "html_content/semester.html"

    with open(input_html_file, "r", encoding="utf-8") as file:
        html_content = file.read()

    print(extract_semester(html_content))
