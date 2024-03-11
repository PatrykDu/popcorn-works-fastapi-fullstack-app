from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from routers import auth

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...),
                        password: str = Form(...), db: Session = Depends(get_db)):

    # checks if username exist
    found_user_model = db.query(models.User).filter(
        models.User.username == username).first()
    if found_user_model is None:
        msg = "Username is not registered"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

    if found_user_model.hashed_password != password:
        msg = "Wrong Password!"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

    return templates.TemplateResponse("customer.html", {"request": request})


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
