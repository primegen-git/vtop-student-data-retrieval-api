import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def extract_cgpa_details(html_content: str) -> Optional[Dict[str, Any]]:
    try:
        if not html_content:
            logger.error("HTML content is empty.")
            return None

        soup = BeautifulSoup(html_content, "html.parser")

        cgpa_table = soup.find("table", class_="table table-hover table-bordered")
        if not cgpa_table:
            logger.warning("CGPA table with the specified class not found in HTML.")
            return None

        tbody = cgpa_table.find("tbody")
        if not tbody:
            logger.warning("CGPA table tbody not found.")
            return None

        tr = tbody.find("tr")
        if not tr:
            logger.warning("CGPA table row not found.")
            return None

        data_cells = tr.find_all("td")
        if len(data_cells) < 11:
            logger.warning("Not enough data cells in CGPA table row.")
            return None

        values = [cell.get_text(strip=True) for cell in data_cells]

        cgpa_details = {
            "registered": float(values[0]),
            "earned": float(values[1]),
            "cgpa": float(values[2]),
            "s-grades": int(values[3]),
            "a-grades": int(values[4]),
            "b-grades": int(values[5]),
            "c-grades": int(values[6]),
            "d-grades": int(values[7]),
            "e-grades": int(values[8]),
            "f-grades": int(values[9]),
            "n-grades": int(values[10]),
        }

        return cgpa_details

    except Exception as e:
        logger.error(f"Error extracting CGPA details: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    input_html_file = "html_content/grade_history.html"

    try:
        with open(input_html_file, "r", encoding="utf-8") as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"Error: '{input_html_file}' not found. Please ensure the file exists.")
        exit()

    cgpa_details = extract_cgpa_details(html_content)
    if cgpa_details:
        print(json.dumps(cgpa_details, indent=4))
    else:
        print("No CGPA details exist.")
