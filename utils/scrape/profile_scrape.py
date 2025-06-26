import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_profile(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        div_element = soup.find("div", attrs={"class": "content"})
        response = {}
        if div_element:
            p_element = div_element.find("p")
            if p_element:
                response["name"] = p_element.get_text().strip()
            register_number_element = div_element.find("label", attrs={"for": "no"})
            if register_number_element:
                response["registration_number"] = (
                    register_number_element.get_text().strip()
                )
            branch_name_element = div_element.find("label", attrs={"for": "branchno"})
            if branch_name_element:
                response["branch_name"] = branch_name_element.get_text().strip()
            return response
        logger.warning("Profile content div not found in HTML.")
        return None
    except Exception as e:
        logger.error(f"Error extracting profile: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    file_location = "html_content/profile.html"

    with open(file_location, "r") as f:
        html_content = f.read()

    response = extract_profile(html_content)
