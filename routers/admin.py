from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
import models
from database import SessionLocal, engine
from utils import get_db

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {"user": "Not authorized"}}
)


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):

    return templates.TemplateResponse("admin.html", {"request": request})
