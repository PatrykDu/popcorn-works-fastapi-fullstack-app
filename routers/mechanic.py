from typing import List
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from utils import get_db, check_user_role_and_redirect, get_current_user

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/mechanic",
    tags=["mechanic"],
    responses={401: {"user": "Not authorized"}}
)


@router.get("/", response_class=HTMLResponse)
async def mechanic_home_page(request: Request, db: Session = Depends(get_db)):
    """Get request for starting mechanic page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    messages = db.query(models.Message).all()

    return templates.TemplateResponse("mechanic.html", {"request": request, "user": user, "messages": messages})


@router.get("/repairs", response_class=HTMLResponse)
async def repairs_page_for_mechanic(request: Request, db: Session = Depends(get_db)):
    """Get request for starting mechanic page after beeing logged in"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    return templates.TemplateResponse("repairs_mechanic.html", {"request": request, "user": user})


@router.get("/storage", response_class=HTMLResponse)
async def storage_page(request: Request, nr_oem: str | None = None,
                       qr_code: str | None = None, search_name: str | None = None,
                       db: Session = Depends(get_db)):
    """Get request for starting mechanic page after beeing logged in"""

    # redirection if not authorized user is trying to reach endpoint
    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']
    user_decoded = get_current_user(request)
    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    # fetch all parts from DB
    found_parts = db.query(models.Part).all()
    parts = []

    # query parameters filtering
    if search_name == '':
        search_name = None
    if nr_oem == '':
        nr_oem = None
    if qr_code == '':
        qr_code = None

    if nr_oem is not None:
        for part in found_parts:
            if part.nr_oem == nr_oem:
                parts.append(part)
    elif qr_code is not None:
        for part in found_parts:
            if part.qr_code == qr_code:
                parts.append(part)

    # filtering name in search
    elif search_name is not None:
        phrases = search_name.split(' ')
        searched_phrases = [phase.casefold() for phase in phrases]
        for part in found_parts:
            part_words: List[str] = part.name.split()
            part_words = [word.casefold() for word in part_words]
            if any(phrase in searched_phrases for phrase in part_words):
                parts.append(part)
    else:
        parts = found_parts

    return templates.TemplateResponse("storage.html", {"request": request, "user": user, "parts": parts})


@router.post("/storage", response_class=HTMLResponse)
async def add_new_part(request: Request, new_part_name: str = Form(...),
                       new_part_amount: int = Form(...), new_part_engine_type: str = Form(...),
                       new_part_price: float = Form(...), new_part_nr_oem: str = Form(...),
                       new_part_qr_code: str = Form(''), db: Session = Depends(get_db)):
    """Post request for adding new parts to the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    part_model = models.Part()

    part_model.name = new_part_name
    part_model.amount_left = new_part_amount
    part_model.engine_type = new_part_engine_type
    part_model.price = new_part_price
    part_model.nr_oem = new_part_nr_oem
    part_model.qr_code = new_part_qr_code

    try:
        db.add(part_model)
        db.commit()
        msg = 'Dodano część'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    return templates.TemplateResponse("storage.html", {"request": request, "user": user, "msg": msg})
    # return RedirectResponse(url="/storage", status_code=status.HTTP_302_FOUND)


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page_for_mechanic(request: Request, db: Session = Depends(get_db)):
    """Get request for starting mechanic page after beeing logged in"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    return templates.TemplateResponse("mechanic_calendar.html", {"request": request, "user": user})
