import httpx
from fastapi import HTTPException
import logging
import time

logger = logging.getLogger(__name__)

sessions = {}
csrf_store = {}


SESSION_TIMEOUT = 3600  # session timeout in 1 hour


async def delete_session(reg_no: str) -> None:
    try:
        del sessions[reg_no]
        logger.info("client is deleteed")
    except Exception as e:
        logger.error(f"error in deleting client {reg_no} : error -> {e}")
        raise HTTPException(500, detail="some internal error")


async def delete_csrf_token(reg_no: str) -> None:
    try:
        del csrf_store[reg_no]
        logger.info("csrf token removed")
    except Exception as e:
        logger.error(f"error in deleting client {reg_no} : error -> {e}")
        raise HTTPException(500, detail="some internal error")


async def store_client(reg_no: str, client: httpx.AsyncClient) -> None:
    try:
        sessions[reg_no] = (client, time.time())
        logger.info(f"Stored client for reg_no: {reg_no}")
    except Exception as e:
        logger.error(f"Error storing client for reg_no {reg_no}: {e}", exc_info=True)
        raise HTTPException(500, detail="internal server error")


async def get_client(reg_no: str) -> httpx.AsyncClient | None:
    try:
        entry = sessions[reg_no]
        if entry:
            client, timeout = entry
            if time.time() - timeout <= SESSION_TIMEOUT:
                return client
            else:
                await delete_session(reg_no)
                logger.error(f"session timeout for {reg_no}")
                return None
        if entry is None:
            logger.warning(f"No client found for reg_no: {reg_no}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving client for reg_no {reg_no}: {e}", exc_info=True)
        return None


async def validate_session(reg_no: str):
    if reg_no not in sessions:
        logger.error(f"Session does not exist for reg_no: {reg_no}")
        raise HTTPException(401, detail="session does not exist")


async def store_csrf(reg_no: str, csrf_token):
    if csrf_token is None:
        logger.error(f"CSRF token does not exist for reg_no: {reg_no}")
        raise ValueError("csrf_token does not exist")
    csrf_store[reg_no] = (csrf_token, time.time())
    logger.info(f"Stored CSRF token for reg_no: {reg_no}")


async def get_csrf(reg_no: str):
    try:
        entry = csrf_store[reg_no]
        if entry:
            csrf, timestamp = entry
            if time.time() - timestamp <= SESSION_TIMEOUT:
                return csrf
            else:
                await delete_session(reg_no)
                logger.error("session expire for csrf token")
                return None
        else:
            logger.warning(f"No CSRF token found for reg_no: {reg_no}")
        return None
    except Exception as e:
        logger.error(
            f"Error retrieving CSRF token for reg_no {reg_no}: {e}", exc_info=True
        )
        return None


async def cleanup_sessions():
    now = time.time()
    expires = [
        reg_no
        for reg_no, (_, timeout) in sessions.items()
        if now - timeout > SESSION_TIMEOUT
    ]
    for reg_no in expires:
        await delete_session(reg_no)
        await delete_csrf_token(reg_no)
        logger.info(f"{reg_no} session is delete due to timeout")
