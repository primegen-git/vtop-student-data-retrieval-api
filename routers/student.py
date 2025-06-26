from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from pydantic import BaseModel
import httpx
from uuid import uuid4


from utils.scrape import login_scrape as sc
from utils.main import VtopScraper

from utils.validator import (
    get_client,
    get_csrf,
    store_csrf,
    validate_session,
    store_client,
)


from database import get_db


router = APIRouter()

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


logger = logging.getLogger(__name__)


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


async def scrape_user_data(session_id: str, reg_no: str):
    client = await get_client(session_id)
    if client is None:
        raise HTTPException(401, "session does not exist")

    csrf_token = await get_csrf(session_id)
    db_gen = get_db()
    db = next(db_gen)

    try:
        scrape = VtopScraper(client, session_id, csrf_token, reg_no, db)

        await scrape.scrape_all()

    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


BASE_URL = "https://vtopcc.vit.ac.in"


@router.get("/create_session")
async def create_session():
    session_id = str(uuid4())
    client = httpx.AsyncClient(
        verify=False, follow_redirects=True
    )  # each client object has its own cookie jar
    await store_client(session_id, client)
    return session_id


@router.post("/prepare_login", response_model=PreLoginResponseModel)
async def prepare_vtop_login(session_id: str):

    await validate_session(session_id)
    client = await get_client(session_id)

    if not client:
        raise HTTPException(500, "client does not exist")

    open_page_url = f"{BASE_URL}/vtop/open/page"

    try:
        attempt = 3
        image_code = None

        while attempt != 0:
            print("enter the client session")
            response = await client.get(url=open_page_url)
            response.raise_for_status()

            csrf_token = sc.extract_csrf_from_open_page(response.text)

            if csrf_token is None:
                raise ValueError("error in getting the csrf token")

            await store_csrf(session_id, csrf_token)

            print("get the session token")

            prelogin_payload = {"_csrf": csrf_token, "flag": "VTOP"}
            prelogin_url = f"{BASE_URL}/vtop/prelogin/setup"

            response = await client.post(
                url=prelogin_url,
                data=prelogin_payload,
                follow_redirects=True,
            )
            response.raise_for_status()

            is_image, image_code = sc.extract_image_recaptcha(response.text)

            if is_image:
                break

            attempt -= 1

        if attempt == 0:
            raise HTTPException(400, detail="failed to retrive image recaptcha")

        return PreLoginResponseModel(success=True, image_code=image_code)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@router.post("/login", response_model=LoginResponseModel)
async def login(login_request: LoginModel, background_tasks: BackgroundTasks):

    await validate_session(login_request.session_id)
    client = await get_client(login_request.session_id)

    if client is None:
        logger.error("client does not exist", exc_info=True)
        raise HTTPException(401, detail="session does not exist")

    try:
        login_url = f"{BASE_URL}/vtop/login"
        print(login_url)

        login_payload = {
            "username": login_request.username,
            "password": login_request.password,
            "captchaStr": login_request.response_captcha,
            "_csrf": await get_csrf(login_request.session_id),
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{BASE_URL}/vtop/login",
        }

        print(f"send request to login_url :{login_url}")
        login_response = await client.post(
            url=login_url, data=login_payload, headers=headers, follow_redirects=True
        )

        try:
            logger.info("login response successful")
            login_response.raise_for_status()
        except Exception as e:
            logger.error(f"error in login request : {str(e)}", exc_info=True)
            return LoginResponseModel(
                success=False, message=f"error in request : {str(e)}"
            )

        print(f"request to login successful")

        redirected_url = str(login_response.url)

        print(f"redirect_url : {redirected_url}")

        if "error" in redirected_url:
            print("error in the login")
            message = sc.extract_error_message(login_response.text)
            if message is None:
                raise ValueError("does not get error message")
            return LoginResponseModel(success=False, message=message)

        if "content" in redirected_url:
            print(f"login passed")

            csrf_token = sc.extract_csrf_from_content_page(login_response.text)

            if csrf_token is None:
                raise ValueError("csrf token does not exist")

            print(f"csrf_token for content page: {csrf_token}")

            await store_csrf(login_request.session_id, csrf_token)

            background_tasks.add_task(
                scrape_user_data, login_request.session_id, login_request.username
            )

            return LoginResponseModel(success=True)

        return LoginResponseModel(success=False, message="unexcepted error in login")

    except Exception as e:
        raise HTTPException(500, detail="error in requests")
