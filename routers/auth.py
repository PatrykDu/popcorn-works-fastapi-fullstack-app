from typing import Optional
from starlette.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import models
from database import SessionLocal, engine
from utils import get_db, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError


templates = Jinja2Templates(directory="templates")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


# def get_password_hash(password):
#     return bcrypt_context.hash(password)


# def verify_password(plain_password, hashed_password):
#     return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.User).filter(
        models.User.username == username).first()

    if not user:
        return False
    if password != user.hashed_password:
        return False
    return user


def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):

    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data['username'], form_data['password'], db)
    if not user:
        return False
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=token_expires)

    response.set_cookie(key="access_token", value=token, httponly=True)

    return True


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:

        form_data = {"request": request,
                     "username": username, "password": password}

        user_model = db.query(models.User).filter(
            models.User.username == username).first()

        if user_model.role == 'mechanic':
            response = RedirectResponse(
                url="/mechanic", status_code=status.HTTP_302_FOUND)
        if user_model.role == 'customer':
            response = RedirectResponse(
                url="/customer", status_code=status.HTTP_302_FOUND)
        if user_model.role == 'admin':
            response = RedirectResponse(
                url="/admin", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, form_data=form_data, db=db)

        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get("/register", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...), username: str = Form(...),
                        firstname: str = Form(...), lastname: str = Form(...),
                        password: str = Form(...), password2: str = Form(...),
                        db: Session = Depends(get_db)):

    # checks if username in DB
    validation1 = db.query(models.User).filter(
        models.User.username == username).first()

    # checks if email in DB
    validation2 = db.query(models.User).filter(
        models.User.email == email).first()

    if password != password2:
        msg = "Verify password must be the same"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})
    if validation1 is not None or validation2 is not None:
        msg = "Username or Email is already in use"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

    user_model = models.User()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname

    user_model.hashed_password = password

    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
