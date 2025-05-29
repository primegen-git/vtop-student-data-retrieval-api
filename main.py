from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from httpx import Cookies
from uuid import uuid4
from utils import scrape as sc

sessions = {}

app = FastAPI()


class LoginModel(BaseModel):
    username: str
    password: str
    session_id: str


class PreLoginResponseModel(BaseModel):
    success: bool
    image_code: str | None


def set_cookies(session_id: str, cookies: Cookies) -> None:
    sessions[session_id] = cookies


def get_cookies(session_id: str) -> Cookies | None:
    return sessions.get(session_id)


BASE_URL = "https://vtopcc.vit.ac.in"


@app.get("/create_session")
async def create_session():
    session_id = str(uuid4())
    sessions[session_id] = None

    return session_id


@app.post("/prepare_login", response_model=PreLoginResponseModel)
async def prepare_vtop_login(session_id: str):

    # check if the session for the user exist or not

    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="sesion not created")

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
                set_cookies(session_id, response.cookies)

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

                set_cookies(session_id, response.cookies)

                is_image, image_code = sc.extract_image_recaptcha(response.text)

                if is_image:
                    break

                attempt -= 1

        if attempt == 0:
            raise HTTPException(400, detail="failed to retrive image recaptcha")

        return PreLoginResponseModel(success=True, image_code=image_code)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
