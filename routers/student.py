from fastapi import APIRouter, Depends, HTTPException
import logging
from pydantic import BaseModel
import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

import models
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

logger = logging.getLogger(__name__)


class LoginModel(BaseModel):
    reg_no: str
    password: str
    response_captcha: str


class PreLoginResponseModel(BaseModel):
    success: bool
    image_code: str | None


class LoginResponseModel(BaseModel):
    success: bool
    message: str | None = None


class LogoutResponseModel(BaseModel):
    success: bool


class ScrapeResponseModel(BaseModel):
    success: bool
    name: str | None


async def scrape_user_data(reg_no: str):
    """
    call the main vtopScrapper calls method scrape() which holds the logic of scraping the data.
    """
    client = await get_client(reg_no)
    if client is None:
        logger.error("Session does not exist for reg_no: %s", reg_no)
        raise HTTPException(401, "session does not exist")

    csrf_token = await get_csrf(reg_no)
    db_gen = get_db()
    db = next(db_gen)

    try:
        scrape = VtopScraper(client, reg_no, csrf_token, db)
        logger.info("Starting scrape for user: %s", reg_no)
        return await scrape.scrape_all()
    except Exception as e:
        logger.error(f"Error in scrape_user_data: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error during scraping")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


BASE_URL = "https://vtopcc.vit.ac.in"


@router.get("/create_session")
async def create_session(reg_no: str):
    try:
        timeout = httpx.Timeout(
            connect=10.0,    # Connection timeout
            read=30.0,  # Read timeout (increase this)
            write=10.0,      # Write timeout
            pool=10.0        # Pool timeout
        )
        client = httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout)
        await store_client(reg_no, client)
        logger.info("Session created for reg_no: %s", reg_no)
        return {
            "success": True,
            "message": "Session created",
        }  # changed: added return statement
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(500, "Failed to create session")


@router.post("/prepare_login", response_model=PreLoginResponseModel)
async def prepare_vtop_login(reg_no: str):
    try:
        await validate_session(reg_no)
        client = await get_client(reg_no)

        if not client:
            logger.error("Client does not exist for reg_no: %s", reg_no)
            raise HTTPException(500, "client does not exist")

        open_page_url = f"{BASE_URL}/vtop/open/page"
        attempt = 3
        image_code = None

        while attempt != 0:
            logger.info("Attempting to get image captcha, attempts left: %d", attempt)
            response = await client.get(url=open_page_url)
            response.raise_for_status()

            csrf_token = sc.extract_csrf_from_open_page(response.text)

            if csrf_token is None:
                logger.error("Failed to get CSRF token")
                raise ValueError("error in getting the csrf token")

            await store_csrf(reg_no, csrf_token)

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
                logger.info("Image captcha retrieved successfully")
                break

            attempt -= 1

        if attempt == 0:
            logger.error("Failed to retrieve image recaptcha after 3 attempts")
            raise HTTPException(400, detail="failed to retrive image recaptcha")

        return PreLoginResponseModel(success=True, image_code=image_code)
    except Exception as e:
        logger.error(f"Error in prepare_vtop_login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{e}")


@router.post("/login", response_model=LoginResponseModel)
async def login(login_request: LoginModel):
    try:
        await validate_session(login_request.reg_no)
        client = await get_client(login_request.reg_no)

        if client is None:
            logger.error("Client does not exist for reg_no: %s", login_request.reg_no)
            raise HTTPException(401, detail="session does not exist")

        login_url = f"{BASE_URL}/vtop/login"
        logger.info(f"Login URL: {login_url}")

        login_payload = {
            "username": login_request.reg_no,
            "password": login_request.password,
            "captchaStr": login_request.response_captcha,
            "_csrf": await get_csrf(login_request.reg_no),
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{BASE_URL}/vtop/login",
        }

        logger.info(f"Sending login request to: {login_url}")
        login_response = await client.post(
            url=login_url, data=login_payload, headers=headers, follow_redirects=True
        )

        try:
            logger.info("Login response received")
            login_response.raise_for_status()
        except Exception as e:
            logger.error(f"Error in login request : {str(e)}", exc_info=True)
            return LoginResponseModel(
                success=False, message=f"error in request : {str(e)}"
            )

        redirected_url = str(login_response.url)
        logger.info(f"Redirected URL after login: {redirected_url}")

        if "error" in redirected_url:
            logger.warning("Error detected in login redirect URL")
            message = sc.extract_error_message(login_response.text)
            if message is None:
                logger.error("No error message found in login response")
                raise ValueError("does not get error message")
            return LoginResponseModel(success=False, message=message)

        if "content" in redirected_url:
            logger.info("Login successful, extracting CSRF token for content page")
            csrf_token = sc.extract_csrf_from_content_page(login_response.text)

            if csrf_token is None:
                logger.error("CSRF token for content page does not exist")
                raise ValueError("csrf token does not exist")

            await store_csrf(login_request.reg_no, csrf_token)

            return LoginResponseModel(success=True)

        logger.error("Unexpected error in login flow")
        return LoginResponseModel(
            success=False, message="unexpected error in login"
        )  # changed: typo fixed in message

    except Exception as e:
        logger.error(f"Error in login endpoint: {e}", exc_info=True)
        raise HTTPException(500, detail="error in requests")


@router.get("/start-scraping", response_model=ScrapeResponseModel)
async def scrape(reg_no: str):
    try:
        await validate_session(reg_no)
        name = await scrape_user_data(reg_no)
        logger.info("Scraping completed for reg_no: %s", reg_no)
        return ScrapeResponseModel(success=True, name=name)
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {e}", exc_info=True)
        raise HTTPException(500, detail="error in scraping")


@router.get("/logout", response_model=ScrapeResponseModel)
async def logout(reg_no: str, db: Session = Depends(get_db)):
    try:
        stmt = delete(models.Student).where(models.Student.reg_no == reg_no)
        db.execute(stmt)
        db.commit()
        logger.info("successfully logout and all data is removed")
        return LogoutResponseModel(success=True)
    except Exception as e:
        logger.error(f"Error in logout endpoint: {e}", exc_info=True)
        raise HTTPException(500, detail="errro in logout")
