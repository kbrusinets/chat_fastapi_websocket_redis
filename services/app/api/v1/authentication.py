from fastapi import APIRouter, Depends, Response, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from services.app.schemas import UserData
from services.backend import Backend, get_backend
from services.backend.exceptions import BackendServiceException
from services.db.models import User

router = APIRouter(tags=['login'])

async def get_current_user(
        backend: Annotated[Backend, Depends(get_backend)],
        token: Annotated[str | None, Cookie(alias='access_token')] = None,
) -> User | None:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Access token not found.'
        )
    try:
        user = await backend.auth_module.get_current_user(token)
    except BackendServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e
    return user


@router.post('/login')
async def login(
        backend: Annotated[Backend, Depends(get_backend)],
        resp: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> UserData:
    try:
        user, access_token, refresh_token = await backend.auth_module.login(
            email=form_data.username,
            password=form_data.password)
    except BackendServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    resp.set_cookie(**access_token.model_dump())
    resp.set_cookie(**refresh_token.model_dump())
    return UserData(id=user.id, name=user.name)


@router.post('/login/refresh')
async def login_for_access_token(
        backend: Annotated[Backend, Depends(get_backend)],
        resp: Response,
        access_token: Annotated[str| None, Cookie(alias='access_token')] = None,
        refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing."
        )

    try:
        access_token = await backend.auth_module.refresh_access(refresh_token=refresh_token, cur_access_token=access_token)
    except BackendServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e

    resp.set_cookie(**access_token.model_dump())
    return True


@router.post('/logout')
async def logout(
        resp: Response,
        backend: Annotated[Backend, Depends(get_backend)],
        access_token: Annotated[str| None, Cookie(alias='access_token')] = None,
        refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None
):
    await backend.auth_module.logout(
        access_token=access_token,
        refresh_token=refresh_token)
    resp.delete_cookie(key='access_token')
    resp.delete_cookie(key='refresh_token')
