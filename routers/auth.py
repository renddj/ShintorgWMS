from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import authenticate_user, create_access_token, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ROLE_HOME = {
    "admin": "/dashboard",
    "manager": "/dashboard",
    "storekeeper": "/dashboard",
    "loader": "/dashboard",
    "accountant": "/dashboard",
}


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse(ROLE_HOME.get(user.role, "/dashboard"), status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 480)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
