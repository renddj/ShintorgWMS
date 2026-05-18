from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user, hash_password
from models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ROLES = ["admin", "manager", "storekeeper", "loader", "accountant"]
ROLE_LABELS = {
    "admin": "Администратор",
    "manager": "Менеджер",
    "storekeeper": "Кладовщик",
    "loader": "Грузчик",
    "accountant": "Бухгалтер",
}


@router.get("/users", response_class=HTMLResponse)
def users_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    users = db.query(User).order_by(User.full_name).all()
    return templates.TemplateResponse("users/list.html", {
        "request": request, "user": user, "users": users, "role_labels": ROLE_LABELS
    })


@router.get("/users/new", response_class=HTMLResponse)
def user_new_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("users/form.html", {
        "request": request, "user": user, "edit_user": None, "roles": ROLES, "role_labels": ROLE_LABELS
    })


@router.post("/users/new")
def user_new(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)

    if len(password) < 8:
        return templates.TemplateResponse("users/form.html", {
            "request": request, "user": user, "edit_user": None,
            "roles": ROLES, "role_labels": ROLE_LABELS,
            "error": "Пароль должен содержать не менее 8 символов"
        })

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("users/form.html", {
            "request": request, "user": user, "edit_user": None,
            "roles": ROLES, "role_labels": ROLE_LABELS,
            "error": "Пользователь с таким логином уже существует"
        })

    new_user = User(
        username=username, full_name=full_name, role=role,
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse("/users", 302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def user_edit_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    edit_user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("users/form.html", {
        "request": request, "user": user, "edit_user": edit_user,
        "roles": ROLES, "role_labels": ROLE_LABELS
    })


@router.post("/users/{user_id}/edit")
def user_edit(
    user_id: int,
    request: Request,
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    is_active: str = Form("on"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)

    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        return RedirectResponse("/users", 302)

    edit_user.full_name = full_name
    edit_user.role = role
    edit_user.is_active = (is_active == "on")

    if password:
        if len(password) < 8:
            return templates.TemplateResponse("users/form.html", {
                "request": request, "user": user, "edit_user": edit_user,
                "roles": ROLES, "role_labels": ROLE_LABELS,
                "error": "Пароль должен содержать не менее 8 символов"
            })
        edit_user.password_hash = hash_password(password)

    db.commit()
    return RedirectResponse("/users", 302)
