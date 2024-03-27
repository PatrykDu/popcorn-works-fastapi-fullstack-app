from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi import Depends, APIRouter, Request
import models
from database import engine
from utils import get_db, check_user_role_and_redirect, get_current_user

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {"user": "Not authorized"}}
)


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Get request for starting admin page after beeing logged in"""

    # checks if customer is logged in (if different role then redirection)
    redirection = check_user_role_and_redirect(request, db, 'admin')
    if redirection["is_needed"]:
        return redirection['redirection']

    user = get_current_user(request)

    return templates.TemplateResponse("admin.html", {"request": request, "user": user})
