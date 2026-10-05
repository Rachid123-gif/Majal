from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.config_loader.territory import Localized
from app.security import (
    SESSION_COOKIE,
    Account,
    authenticate,
    create_session_token,
    require_account,
)
from app.settings import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class Me(BaseModel):
    username: str
    display_name: Localized
    roles: list[str]


def _me(account: Account) -> Me:
    return Me(
        username=account.username,
        display_name=Localized(fr=account.display_name_fr, ar=account.display_name_ar),
        roles=[role.value for role in account.roles],
    )


@router.post("/login")
def login(body: LoginRequest, response: Response) -> Me:
    account = authenticate(body.username, body.password)
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(account),
        max_age=settings.session_max_age_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        path="/",
    )
    return _me(account)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(account: Annotated[Account, Depends(require_account)]) -> Me:
    return _me(account)
