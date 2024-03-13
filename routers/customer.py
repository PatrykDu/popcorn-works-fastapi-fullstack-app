from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from utils import get_db, get_current_user, check_user_role_and_redirect

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

    return templates.TemplateResponse("customer.html", {"request": request, "user": user})
