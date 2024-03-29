from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi import Depends, status, APIRouter, Request, Form
import models
from database import engine
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
    """POST request for contact form"""

    message_model = models.Message()
    message_model.email = email
    message_model.message = message

    db.add(message_model)
    db.commit()

    msg = "Message has been sent."
    return templates.TemplateResponse("contact-form.html",
                                      {"request": request, "msg": msg})


@router.get("/delete/{message_id}", response_class=HTMLResponse)
async def delete_message(request: Request, message_id: str,
                         db: Session = Depends(get_db)):
    """GET request for deleting specific message from DB"""

    message_model_to_delete = db.query(models.Message).filter(
        models.Message.id == message_id).first()

    db.delete(message_model_to_delete)
    db.commit()

    return RedirectResponse(url="/mechanic", status_code=status.HTTP_302_FOUND)
