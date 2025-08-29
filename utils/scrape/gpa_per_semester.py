from bs4 import BeautifulSoup
from typing import Optional, Union
import re


def extract_gpa(html_content: str) -> Optional[Union[float, str]]:
    """
    Extracts the GPA value from the grade.html content.
    Returns the GPA as a float if found, else None.
    """
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")

    # Look for a span or bold text with GPA
    # e.g.: <span style="font-size: 18px; font-weight: bold">GPA : 9.07</span>
    gpa_text = None
    for span in soup.find_all("span"):
        text = span.text.strip()
        # Match GPA anywhere in the span text, not just at the start
        if "GPA" in text:
            gpa_text = text
            break
    if not gpa_text:
        text = soup.get_text()
        match = re.search(r"GPA\s*:\s*([0-9]+\.?[0-9]*)", text)
        if match:
            return float(match.group(1))
        return None
    # Extract GPA using regex
    match = re.search(r"GPA\s*:\s*([0-9]+\.?[0-9]*)", gpa_text)
    if match:
        try:
            gpa_value = float(match.group(1))
            return gpa_value
        except ValueError:
            return match.group(1)
    return None
