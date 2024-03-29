from typing import List
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi import Depends, status, APIRouter, Request, Form
import models
from database import engine
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

    all_repairs = db.query(models.Repair).all()

    return templates.TemplateResponse("mechanic.html", {"request": request, "user": user,
                                                        "messages": messages, "repairs": all_repairs})


@router.get("/repairs", response_class=HTMLResponse)
async def repairs_page_for_mechanic(request: Request, db: Session = Depends(get_db)):
    """Get request for starting mechanic page after beeing logged in"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    found_customers = db.query(models.User).filter(
        models.User.role == 'customer')

    repairs = db.query(models.Repair).all()

    return templates.TemplateResponse("repairs_mechanic.html", {"request": request, "user": user,
                                                                "customers": found_customers,
                                                                "repairs": repairs})


@router.post("/repairs", response_class=HTMLResponse)
async def add_new_repair(request: Request, car_name: str = Form(...), customer_id: int = Form(...),
                         start_of_repair: str = Form(...), end_of_repair: str = Form(...),
                         db: Session = Depends(get_db)):
    """Post request for adding new repair to the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    repair_model = models.Repair()

    repair_model.car_name = car_name
    repair_model.start_date = start_of_repair
    repair_model.end_date = end_of_repair
    repair_model.active = True
    repair_model.customer_id = customer_id

    try:
        db.add(repair_model)
        db.commit()
        msg = 'Dodano nowy termin'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    return RedirectResponse(url="/mechanic/repairs", status_code=status.HTTP_302_FOUND)


@router.get("/repairs/{repair_id}", response_class=HTMLResponse)
async def repairs_id_page_for_mechanic(request: Request, repair_id: int, db: Session = Depends(get_db)):
    """Get request for repair_id page"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']
    user_decoded = get_current_user(request)
    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    all_parts = db.query(models.Part).all()
    used_parts = db.query(models.Part).join(models.PartsInRepair, models.Part.id == models.PartsInRepair.part_id).filter(
        models.PartsInRepair.repair_id == repair_id).all()

    for part in used_parts:
        for repair in part.repairs:
            if repair.repair_id != repair_id:
                repair_index = part.repairs.index(repair)
                part.repairs.pop(repair_index)

    total_price = 0
    for part in used_parts:
        total_price += (part.repairs[0].quantity * part.price)

    repair = db.query(models.Repair).filter(
        models.Repair.id == repair_id).first()
    customer = db.query(models.User).filter(
        models.User.id == repair.customer_id).first()

    return templates.TemplateResponse("repairs_mechanic_id.html", {"request": request,
                                                                   "user": user,
                                                                   "all_parts": all_parts,
                                                                   "used_parts": used_parts,
                                                                   "customer": customer,
                                                                   "repair": repair,
                                                                   "total_price": total_price})


@router.post("/repairs/{repair_id}", response_class=HTMLResponse)
async def add_new_part_to_repair_id(request: Request, repair_id: int, part_id: int = Form(...),
                                    quantity: int = Form(...), db: Session = Depends(get_db)):
    """Post request for adding to the DB new part used in repair_id or change date"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    # add new part to repair
    parts_in_repair_model = models.PartsInRepair()
    parts_in_repair_model.part_id = part_id
    parts_in_repair_model.repair_id = repair_id
    parts_in_repair_model.quantity = quantity

    try:
        db.add(parts_in_repair_model)
        db.commit()
        msg = 'Dodano nową część do rachunku'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    url = f"/mechanic/repairs/{repair_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/repairs/delete/{repair_id}", response_class=HTMLResponse)
async def remove_repair(request: Request, repair_id: int,
                        db: Session = Depends(get_db)):
    """Post request for removing repair from the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    repair_model = db.query(models.Repair).filter(
        models.Repair.id == repair_id).first()

    try:
        db.delete(repair_model)
        db.commit()
        msg = 'usunięto'
    except Exception as err:
        msg = f"błąd: {err}"

    return RedirectResponse(url="/mechanic/repairs", status_code=status.HTTP_302_FOUND)


@router.post("/repairs/{repair_id}/change_date", response_class=HTMLResponse)
async def change_date_of_repair(request: Request, repair_id: int, start_of_repair: str = Form(...),
                                end_of_repair: str = Form(...), db: Session = Depends(get_db)):
    """Post request for adding to the DB new part used in repair_id or change date"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    repair = db.query(models.Repair).filter(
        models.Repair.id == repair_id).first()

    # change repair date
    repair.start_date = start_of_repair
    repair.end_date = end_of_repair

    try:
        db.add(repair)
        db.commit()
        msg = 'Zmieniono datę'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    url = f"/mechanic/repairs/{repair_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.post("/repairs/{repair_id}/activate", response_class=HTMLResponse)
async def change_date_of_repair(request: Request, repair_id: int, db: Session = Depends(get_db)):
    """Post request for adding to the DB new part used in repair_id or change date"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    repair = db.query(models.Repair).filter(
        models.Repair.id == repair_id).first()

    # change repair active status
    repair.active = not repair.active

    try:
        db.add(repair)
        db.commit()
        msg = 'Zaktualizowano naprawę'
    except Exception as err:
        msg = f"błąd podczas zmiany: {err}"

    url = f"/mechanic/repairs/{repair_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.post("/repairs/{repair_id}/{used_part_id}", response_class=HTMLResponse)
async def change_amount_of_used_parts(request: Request, repair_id: int, used_part_id: int,
                                      new_amount: int = Form(...), db: Session = Depends(get_db)):
    """Post request for changing amount of used parts in specific repair"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    part_in_repair = db.query(models.PartsInRepair).filter(
        models.PartsInRepair.repair_id == repair_id).filter(models.PartsInRepair.part_id == used_part_id).first()

    # change repair date
    part_in_repair.quantity = new_amount

    try:
        db.add(part_in_repair)
        db.commit()
        msg = 'Zmieniono'
    except Exception as err:
        msg = f"błąd: {err}"

    url = f"/mechanic/repairs/{repair_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.post("/repairs/{repair_id}/delete_part/{used_part_id}", response_class=HTMLResponse)
async def remove_part_from_repair(request: Request, repair_id: int, used_part_id: int, db: Session = Depends(get_db)):
    """Post request removing used part in specific repair"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    part_in_repair = db.query(models.PartsInRepair).filter(
        models.PartsInRepair.repair_id == repair_id).filter(models.PartsInRepair.part_id == used_part_id).first()

    try:
        db.delete(part_in_repair)
        db.commit()
        msg = 'Zmieniono'
    except Exception as err:
        msg = f"błąd: {err}"

    url = f"/mechanic/repairs/{repair_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


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
            part_words: List[str] = part.name.split(' ')
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

    return RedirectResponse(url="/mechanic/storage", status_code=status.HTTP_302_FOUND)


@router.post("/storage/{part_id}", response_class=HTMLResponse)
async def change_part(request: Request, part_id: int, change_part_name: str = Form(...),
                      change_part_left: int = Form(...), change_part_engine: str = Form(...),
                      change_part_price: float = Form(...), change_part_oem: str = Form(...),
                      db: Session = Depends(get_db)):
    """Post request for changing part in the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    part_model = db.query(models.Part).filter(
        models.Part.id == part_id).first()

    part_model.name = change_part_name
    part_model.amount_left = change_part_left
    part_model.engine_type = change_part_engine
    part_model.price = change_part_price
    part_model.nr_oem = change_part_oem

    try:
        db.add(part_model)
        db.commit()
        msg = 'Dodano część'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    return RedirectResponse(url="/mechanic/storage", status_code=status.HTTP_302_FOUND)


@router.post("/storage/delete/{part_id}", response_class=HTMLResponse)
async def change_part(request: Request, part_id: int,
                      db: Session = Depends(get_db)):
    """Post request removing part from the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    part_model = db.query(models.Part).filter(
        models.Part.id == part_id).first()

    try:
        db.delete(part_model)
        db.commit()
        msg = 'Dodano część'
    except Exception as err:
        msg = f"błąd: {err}"

    return RedirectResponse(url="/mechanic/storage", status_code=status.HTTP_302_FOUND)


def convert_repairs(repairs: List[models.Repair]):
    repair_dates = []
    for repair in repairs:
        if repair.active:
            color = "red"
            text = "white"
        else:
            color = "grey"
            text = "black"
        repair_dates.append(
            {
                "title": f"{repair.car_name}",
                "start": f"{repair.start_date}",
                "end": f"{repair.end_date}",
                "color": color,
                "textColor": text,
                "id": f"{repair.id}",
            }
        )
    return repair_dates


@router.get("/calendar", response_class=HTMLResponse)
async def mechanic_calendar(request: Request, db: Session = Depends(get_db)):
    """Get request for customer/repairs page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']
    user = get_current_user(request)

    model_repairs = db.query(models.Repair).all()
    all_repairs = convert_repairs(model_repairs)

    found_customers = db.query(models.User).filter(
        models.User.role == 'customer')

    return templates.TemplateResponse("calendar_mechanic.html", {"request": request,
                                                                 "user": user,
                                                                 "customers": found_customers,
                                                                 "customer_repairs": all_repairs})


@router.post("/calendar", response_class=HTMLResponse)
async def add_new_repair(request: Request, car_name: str = Form(...), customer_id: int = Form(...),
                         start_of_repair: str = Form(...), end_of_repair: str = Form(...),
                         db: Session = Depends(get_db)):
    """Post request for adding new repair to the DB"""

    redirection = check_user_role_and_redirect(request, db, 'mechanic')
    if redirection["is_needed"]:
        return redirection['redirection']

    user_decoded = get_current_user(request)

    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()

    repair_model = models.Repair()

    repair_model.car_name = car_name
    repair_model.start_date = start_of_repair
    repair_model.end_date = end_of_repair
    repair_model.active = True
    repair_model.customer_id = customer_id

    try:
        db.add(repair_model)
        db.commit()
        msg = 'Dodano nową naprawę'
    except Exception as err:
        msg = f"błąd podczas dodawania: {err}"

    return templates.TemplateResponse("success.html", {"request": request, "user": user, "msg": msg})
