from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from utils import get_db, get_current_user, check_user_role_and_redirect
from typing import List

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/customer",
    tags=["customer"],
    responses={401: {"user": "Not authorized"}}
)


@router.get("/", response_class=HTMLResponse)
async def customer_home_page(request: Request, db: Session = Depends(get_db)):
    """Get request for starting customer page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'customer')
    if redirection["is_needed"]:
        return redirection['redirection']

    user = get_current_user(request)

    customer_repairs = db.query(models.Repair).filter(
        models.Repair.customer_id == user['id']).all()

    return templates.TemplateResponse("customer.html", {"request": request,
                                                        "user": user,
                                                        "customer_repairs": customer_repairs})


@router.get("/repairs", response_class=HTMLResponse)
async def customer_home_page(request: Request, db: Session = Depends(get_db)):
    """Get request for customer/repairs page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'customer')
    if redirection["is_needed"]:
        return redirection['redirection']

    user = get_current_user(request)

    customer_repairs = db.query(models.Repair).filter(
        models.Repair.customer_id == user['id']).all()

    return templates.TemplateResponse("repairs_customer.html", {"request": request,
                                                                "user": user,
                                                                "customer_repairs": customer_repairs})


@router.get("/repairs/{repair_id}", response_class=HTMLResponse)
async def repairs_id_page_for_mechanic(request: Request, repair_id: int, db: Session = Depends(get_db)):
    """Get request for repair_id page"""

    redirection = check_user_role_and_redirect(request, db, 'customer')
    if redirection["is_needed"]:
        return redirection['redirection']
    user_decoded = get_current_user(request)
    user = db.query(models.User).filter(
        models.User.username == user_decoded['username']).first()
    used_parts = db.query(models.Part).join(models.PartsInRepair, models.Part.id == models.PartsInRepair.part_id).filter(
        models.PartsInRepair.repair_id == repair_id).all()

    repair = db.query(models.Repair).filter(
        models.Repair.id == repair_id).first()

    return templates.TemplateResponse("repairs_customer_id.html", {"request": request,
                                                                   "user": user,
                                                                   "used_parts": used_parts,
                                                                   "repair": repair})


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
                "textColor": text
            }
        )
    return repair_dates


@router.get("/calendar", response_class=HTMLResponse)
async def customer_home_page(request: Request, db: Session = Depends(get_db)):
    """Get request for customer/repairs page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'customer')
    if redirection["is_needed"]:
        return redirection['redirection']

    user = get_current_user(request)

    model_customer_repairs = db.query(models.Repair).filter(
        models.Repair.customer_id == user['id']).all()

    customer_repairs = convert_repairs(model_customer_repairs)

    return templates.TemplateResponse("calendar_customer.html", {"request": request,
                                                                 "user": user,
                                                                 "customer_repairs": customer_repairs})
