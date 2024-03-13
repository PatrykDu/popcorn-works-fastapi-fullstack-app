from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from utils import get_db, get_current_user

router = APIRouter(
    prefix="/contact",
    tags=["contact"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def contact_page(request: Request, db: Session = Depends(get_db)):

    user = get_current_user(request)

    if user:
        user_model = db.query(models.User).filter(
            models.User.username == user['username']).first()
        if user_model.role == "customer":
            return RedirectResponse(url="/customer", status_code=status.HTTP_302_FOUND)
        if user_model.role == "mechanic":
            return RedirectResponse(url="/mechanic", status_code=status.HTTP_302_FOUND)
        if user_model.role == "admin":
            return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("contact-form.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def message_form(request: Request, email: str = Form(...),
                       message: str = Form(...),
                       db: Session = Depends(get_db)):

    message_model = models.Message()
    message_model.email = email
    message_model.message = message

    db.add(message_model)
    db.commit()

    msg = "Message has been sent."
    return templates.TemplateResponse("contact-form.html",
                                      {"request": request, "msg": msg})
