import httpx
from fastapi import HTTPException

sessions = {}
csrf_store = {}


async def store_client(session_id: str, client: httpx.AsyncClient) -> None:
    try:
        sessions[session_id] = client
    except Exception as e:
        raise HTTPException(500, detail="internal server error")


# NOTE: keeping this in async because eventually it is being replaced by redis instance call
async def get_client(session_id: str) -> httpx.AsyncClient | None:
    return sessions.get(session_id)


async def validate_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(401, detail="session does not exist")


async def store_csrf(session_id: str, csrf_token):
    if csrf_token is None:
        raise ValueError("csrf_token does not exist")
    csrf_store[session_id] = csrf_token


# NOTE: in doubt to keep it or remove it since it is being used only once
async def get_csrf(session_id: str):
    return csrf_store.get(session_id)
