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
    soup = BeautifulSoup(html_content, "html.parser")

    span_tag = soup.find("span", attrs={"role": "alert"})
    if span_tag:
        return span_tag.get_text(strip=True)
    return None


def extract_csrf_from_login_page(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")

    scripts = soup.find_all("scripts")

    csrf_value = None

    for script in scripts:
        if (
            script.string
        ):  # ensure that we only take scripts with javascript embeeded in it and not <script scr="">
            match = re.search(r'var\s+csrf_value\s*=*"([^"]+)', script.string)

            if match:
                csrf_value = match.group(1)
                break

    return csrf_value
