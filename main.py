from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, Request, status
import models
from database import SessionLocal, engine
from routers import auth, customer, mechanic, admin, contact
from utils import get_db, get_current_user, check_user_role_and_redirect

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(mechanic.router)
app.include_router(admin.router)
app.include_router(contact.router)


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Get request of the home page. If user is logged in it will redirect
    him to his starting page, so home screen is available only for
    not logged in users."""

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

    return templates.TemplateResponse("home.html", {"request": request, "user": user})
