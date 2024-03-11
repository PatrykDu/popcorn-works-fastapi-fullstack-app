from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine


router = APIRouter(
    prefix="/contact",
    tags=["contact"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def contact_page(request: Request):

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
