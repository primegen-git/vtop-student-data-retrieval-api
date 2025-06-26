import logging
from inspect import walktree
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


def extract_csrf_from_open_page(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        form_tag = soup.find("form", attrs={"id": "stdForm"})
        if not form_tag:
            logger.warning("Form with id 'stdForm' not found in HTML content.")
            return None
        csrf_input = form_tag.find("input", attrs={"name": "_csrf"})
        if not csrf_input:
            logger.warning("CSRF input with name '_csrf' not found in form.")
            return None
        return csrf_input.get("value", None)
    except Exception as e:
        logger.error(f"Error extracting CSRF from open page: {e}", exc_info=True)
        return None


def extract_image_recaptcha(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        captcha_div_block = soup.find("div", attrs={"id": "captchaBlock"})
        if captcha_div_block:
            img_tag = captcha_div_block.find(
                "img",
                src=lambda s: isinstance(s, str)
                and s.startswith("data:image/jpeg;base64,"),
            )
            if img_tag:
                captcha_img_base64 = img_tag["src"]
                return True, captcha_img_base64
        return False, None
    except Exception as e:
        logger.error(f"Error extracting image recaptcha: {e}", exc_info=True)
        return False, None


def extract_error_message(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        span_tag = soup.find("span", attrs={"role": "alert"})
        if span_tag:
            return span_tag.get_text(strip=True)
        return None
    except Exception as e:
        logger.error(f"Error extracting error message: {e}", exc_info=True)
        return None


def extract_csrf_from_content_page(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        form_tag = soup.find("form", attrs={"id": "logoutForm1"})
        if not form_tag:
            logger.warning("Form with id 'logoutForm1' not found in HTML content.")
            return None
        csrf_tag = form_tag.find("input", attrs={"name": "_csrf"})
        if not csrf_tag:
            logger.warning("CSRF input with name '_csrf' not found in form.")
            return None
        csrf_value = csrf_tag.get("value")
        return csrf_value
    except Exception as e:
        logger.error(f"Error extracting CSRF from content page: {e}", exc_info=True)
        return None

