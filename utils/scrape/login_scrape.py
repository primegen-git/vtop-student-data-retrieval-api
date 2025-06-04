from inspect import walktree
from bs4 import BeautifulSoup
import re


def extract_csrf_from_open_page(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")

    form_tag = soup.find("form", attrs={"id": "stdForm"})

    if not form_tag:
        return None

    csrf_input = form_tag.find("input", attrs={"name": "_csrf"})

    if not csrf_input:
        return None

    return csrf_input.get("value", None)


def extract_image_recaptcha(html_content: str):

    print("inside time image recaptcha method")

    soup = BeautifulSoup(html_content, "html.parser")

    captcha_div_block = soup.find("div", attrs={"id": "captchaBlock"})

    if captcha_div_block:
        print(f"captcha div block found")

        img_tag = captcha_div_block.find(
            "img",
            src=lambda s: isinstance(s, str)
            and s.startswith("data:image/jpeg;base64,"),
        )
        if img_tag:

            print(f"captcha image tag found")

            captcha_img_base64 = img_tag["src"]
            return True, captcha_img_base64

    print("does not find image tag")

    return False, None


def extract_error_message(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        span_tag = soup.find("span", attrs={"role": "alert"})
        if span_tag:
            return span_tag.get_text(strip=True)
        return None
    except Exception as e:
        print(f"error in extracting login-error-msg : {str(e)}")


def extract_csrf_from_content_page(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        form_tag = soup.find("form", attrs={"id": "logoutForm1"})

        if not form_tag:
            print("Form with id 'logoutForm1' not found.")
            return None

        csrf_tag = form_tag.find("input", attrs={"name": "_csrf"})
        if not csrf_tag:
            print("CSRF input tag not found inside the form.")
            return None

        csrf_value = csrf_tag.get("value")
        return csrf_value

    except Exception as e:
        print(f"Some error in extracting login CSRF: {str(e)}")
        return None
