from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, Request
import models
from database import SessionLocal, engine
from routers import auth, customer
from utils import get_db

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


app.include_router(auth.router)
app.include_router(customer.router)


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):

    return templates.TemplateResponse("home.html", {"request": request})
