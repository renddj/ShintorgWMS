from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.task_service import create_task, plan_task, close_task, report_problem, cancel_task
from models.task import Task
from models.product import Product, StockLocation
from models.address import StorageAddress, Zone

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
        tasks = db.query(Task).filter(
            Task.status.in_(["new", "in_progress", "problem"])
        ).order_by(Task.created_at).all()
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
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    return templates.TemplateResponse("tasks/form.html", {"request": request, "user": user, "products": products, "addresses": addresses})


@router.post("/tasks/new")
def task_new(
    request: Request,
    task_type: str = Form(...),
    product_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    to_address_id: int = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "manager"):
        return RedirectResponse("/dashboard", 302)

    task, error = create_task(db, task_type, product_id, quantity, user.id, comment or None, to_address_id)
    if error:
        products = db.query(Product).order_by(Product.name).all()
        addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
        return templates.TemplateResponse("tasks/form.html", {
            "request": request, "user": user, "products": products, "addresses": addresses, "error": error
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

    # Для планирования — передаём локации с остатками
    locations = []
    if task.status == "new" and user.role == "storekeeper":
        if task.task_type == "shipment":
            locations = db.query(StockLocation).filter(
                StockLocation.product_id == task.product_id,
                StockLocation.quantity > 0,
            ).all()
        else:  # receipt — все адреса
            locations = db.query(StockLocation).filter(
                StockLocation.product_id == task.product_id,
            ).all()
            # Добавляем адреса где товара нет вообще (пустые)
            used_addr_ids = {l.address_id for l in locations}
            all_addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
            for addr in all_addresses:
                if addr.id not in used_addr_ids:
                    locations.append(type("FakeLoc", (), {
                        "address_id": addr.id,
                        "address": addr,
                        "quantity": 0,
                        "reserved_quantity": 0,
                        "available": 0,
                    })())

    return templates.TemplateResponse("tasks/detail.html", {
        "request": request, "user": user, "task": task, "locations": locations
    })


@router.post("/tasks/{task_id}/plan")
async def task_plan(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "storekeeper":
        return RedirectResponse("/dashboard", 302)

    form = await request.form()
    lines = []
    for key, value in form.items():
        if key.startswith("qty_"):
            try:
                addr_id = int(key.split("_")[1])
                qty = float(value)
                if qty > 0:
                    lines.append({"address_id": addr_id, "quantity": qty})
            except (ValueError, IndexError):
                pass

    task, error = plan_task(db, task_id, user.id, lines)
    if error:
        task = db.query(Task).filter(Task.id == task_id).first()
        locations = db.query(StockLocation).filter(
            StockLocation.product_id == task.product_id,
        ).all()
        if task.task_type == "receipt":
            used_addr_ids = {l.address_id for l in locations}
            all_addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
            for addr in all_addresses:
                if addr.id not in used_addr_ids:
                    locations.append(type("FakeLoc", (), {
                        "address_id": addr.id, "address": addr,
                        "quantity": 0, "reserved_quantity": 0, "available": 0,
                    })())
        return templates.TemplateResponse("tasks/detail.html", {
            "request": request, "user": user, "task": task,
            "locations": locations, "error": error
        })
    return RedirectResponse(f"/tasks/{task_id}", 302)


@router.post("/tasks/{task_id}/problem")
def task_problem(task_id: int, request: Request,
                 problem_comment: str = Form(...), db: Session = Depends(get_db)):
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
    close_task(db, task_id, user.id)
    return RedirectResponse(f"/tasks/{task_id}", 302)


@router.post("/tasks/{task_id}/cancel")
def task_cancel(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "manager"):
        return RedirectResponse("/dashboard", 302)
    cancel_task(db, task_id)
    return RedirectResponse("/tasks", 302)
