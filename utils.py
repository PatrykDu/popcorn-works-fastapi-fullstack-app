import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request, Depends, status
from starlette.responses import RedirectResponse
from jose import jwt, JWTError
from database import SessionLocal, engine
import models

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            # logout(request)
            pass
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="Not found")


def check_user_role_and_redirect(request: Request, db, role: str):
    user = get_current_user(request)

    redirection = {"is_needed": False, 'redirection': None}
    if user is None:
        redirection['redirection'] = RedirectResponse(
            url="/login", status_code=status.HTTP_302_FOUND)
        redirection["is_needed"] = True
    else:
        user_model = db.query(models.User).filter(
            models.User.username == user['username']).first()
        if user_model.role != role:
            if user_model.role == "customer":
                redirection['redirection'] = RedirectResponse(
                    url="/customer", status_code=status.HTTP_302_FOUND)
                redirection["is_needed"] = True
            if user_model.role == "mechanic":
                redirection['redirection'] = RedirectResponse(
                    url="/mechanic", status_code=status.HTTP_302_FOUND)
                redirection["is_needed"] = True
            if user_model.role == "admin":
                redirection['redirection'] = RedirectResponse(
                    url="/admin", status_code=status.HTTP_302_FOUND)
                redirection["is_needed"] = True
    return redirection
