from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.task_service import create_task, take_task, close_task, report_problem, cancel_task
from models.task import Task
from models.product import Product

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/tasks", response_class=HTMLResponse)
def tasks_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)

    if user.role in ("admin", "manager"):
        tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    elif user.role == "storekeeper":
        tasks = db.query(Task).filter(Task.status.in_(["new", "in_progress", "problem"])).order_by(Task.created_at).all()
    elif user.role == "loader":
        tasks = db.query(Task).filter(Task.status == "in_progress").order_by(Task.created_at).all()
    else:
        tasks = db.query(Task).filter(Task.status == "done").order_by(Task.closed_at.desc()).all()

    return templates.TemplateResponse("tasks/list.html", {"request": request, "user": user, "tasks": tasks})


@router.get("/tasks/new", response_class=HTMLResponse)
def task_new_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "manager"):
        return RedirectResponse("/dashboard", 302)
    products = db.query(Product).order_by(Product.name).all()
    return templates.TemplateResponse("tasks/form.html", {"request": request, "user": user, "products": products})


@router.post("/tasks/new")
def task_new(
    request: Request,
    product_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "manager"):
        return RedirectResponse("/dashboard", 302)

    task, error = create_task(db, product_id, quantity, user.id, comment or None)
    if error:
        products = db.query(Product).order_by(Product.name).all()
        return templates.TemplateResponse("tasks/form.html", {
            "request": request, "user": user, "products": products, "error": error
        })
    return RedirectResponse("/tasks", 302)


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
def task_detail(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return RedirectResponse("/tasks", 302)
    return templates.TemplateResponse("tasks/detail.html", {"request": request, "user": user, "task": task})


@router.post("/tasks/{task_id}/take")
def task_take(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "storekeeper":
        return RedirectResponse("/dashboard", 302)
    take_task(db, task_id, user.id)
    return RedirectResponse(f"/tasks/{task_id}", 302)


@router.post("/tasks/{task_id}/problem")
def task_problem(
    task_id: int, request: Request,
    problem_comment: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "storekeeper":
        return RedirectResponse("/dashboard", 302)
    report_problem(db, task_id, user.id, problem_comment)
    return RedirectResponse(f"/tasks/{task_id}", 302)


@router.post("/tasks/{task_id}/close")
def task_close(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "storekeeper":
        return RedirectResponse("/dashboard", 302)
    task, error = close_task(db, task_id, user.id)
    return RedirectResponse(f"/tasks/{task_id}", 302)


@router.post("/tasks/{task_id}/cancel")
def task_cancel(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "manager"):
        return RedirectResponse("/dashboard", 302)
    cancel_task(db, task_id)
    return RedirectResponse("/tasks", 302)
