from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from httpx import Cookies
from uuid import uuid4

from utils import scrape as sc

sessions = {}
csrf_store = {}

app = FastAPI()


class LoginModel(BaseModel):
    username: str
    password: str
    response_captcha: str
    session_id: str


class PreLoginResponseModel(BaseModel):
    success: bool
    image_code: str | None


class LoginResponseModel(BaseModel):
    success: bool
    message: str | None = None


def store_cookies(session_id: str, cookies: Cookies) -> None:
    sessions[session_id] = cookies


def get_cookies(session_id: str) -> Cookies | None:
    return sessions.get(session_id)


def validate_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(401, detail="session does not exist")


def store_csrf(session_id: str, csrf_token):
    if csrf_token is None:
        raise ValueError("csrf_token does not exist")
    csrf_store[session_id] = csrf_token


def get_csrf(session_id: str):
    return csrf_store.get(session_id)


BASE_URL = "https://vtopcc.vit.ac.in"


@app.get("/create_session")
async def create_session():
    session_id = str(uuid4())
    sessions[session_id] = None

    return session_id


@app.post("/prepare_login", response_model=PreLoginResponseModel)
async def prepare_vtop_login(session_id: str):

    # check if the session for the user exist or not

    validate_session(session_id)

    open_page_url = f"{BASE_URL}/vtop/open/page"

    try:

        # NOTE: change this variable to be imported from env variable
        attempt = 3
        image_code = None

        while attempt != 0:
            async with httpx.AsyncClient(verify=False) as client:
                print("enter the client session")
                response = await client.get(url=open_page_url)
                response.raise_for_status()
                store_cookies(session_id, response.cookies)

                # NOTE: Testing purpose only
                # with open("html_content/open_page.txt", "w", encoding="utf-8") as file:
                #     file.write(str(response.text))
                #     file.newlines
                #     file.write(str(response.headers))
                #     file.newlines
                #     file.write(str(response.cookies))

                csrf_token = sc.extract_csrf_from_open_page(response.text)

                if csrf_token is None:
                    raise ValueError("error in getting the csrf token")

                store_csrf(session_id, csrf_token)

                print("get the session token")

                prelogin_payload = {"_csrf": csrf_token, "flag": "VTOP"}
                prelogin_url = f"{BASE_URL}/vtop/prelogin/setup"

                cookies = get_cookies(session_id)
                response = await client.post(
                    url=prelogin_url,
                    cookies=cookies,
                    data=prelogin_payload,
                    follow_redirects=True,
                )
                response.raise_for_status()
                # print(f"{response.url}")

                store_cookies(session_id, response.cookies)

                is_image, image_code = sc.extract_image_recaptcha(response.text)

                if is_image:
                    break

                attempt -= 1

        if attempt == 0:
            raise HTTPException(400, detail="failed to retrive image recaptcha")

        return PreLoginResponseModel(success=True, image_code=image_code)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@app.post("/login", response_model=LoginResponseModel)
async def login(login_request: LoginModel):

    validate_session(login_request.session_id)
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            login_url = f"{BASE_URL}/vtop/login"
            print(login_url)
            cookies = get_cookies(login_request.session_id)
            login_payload = {
                "username": login_request.username,
                "password": login_request.password,
                "captchaStr": login_request.response_captcha,
                "_csrf": get_csrf(login_request.session_id),
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{BASE_URL}/vtop/login",
            }

            print(f"send request to login_url :{login_url}")
            login_response = await client.post(
                url=login_url, data=login_payload, cookies=cookies, headers=headers
            )

            try:
                login_response.raise_for_status()
            except Exception as e:
                return LoginResponseModel(
                    success=False, message=f"error in request : str{e}"
                )

            store_cookies(login_request.session_id, login_response.cookies)
            print(f"request to login successful")

            redirected_url = str(login_response.url)

            print(f"redirect_url : {redirected_url}")

            if "error" in redirected_url:
                message = sc.extract_error_message(login_response.text)
                if message is None:
                    raise ValueError("does not get error message")
                return LoginResponseModel(success=False, message=message)

            if "content" in redirected_url:
                csrf_token = sc.extract_csrf_from_login_page(login_response.text)
                if csrf_token is None:
                    raise ValueError("csrf token does not exist")

                store_csrf(login_request.session_id, csrf_token)
                return LoginResponseModel(success=True)

            return LoginResponseModel(
                success=False, message="unexcepted error in login"
            )

    except Exception as e:
        raise HTTPException(500, detail="error in requests")
