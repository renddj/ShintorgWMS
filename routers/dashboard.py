from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from services.auth_service import get_current_user
from models.task import Task
from models.product import Product, StockLocation

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)
    return RedirectResponse("/dashboard", 302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)

    ctx = {"request": request, "user": user}

    if user.role in ("admin", "manager"):
        active_count = db.query(Task).filter(Task.status.in_(["new", "in_progress"])).count()
        problem_count = db.query(Task).filter(Task.status == "problem").count()

        
        products = db.query(Product).filter(Product.min_quantity > 0).all()
        low_stock_count = sum(1 for p in products if p.is_low_stock)

        recent_tasks = db.query(Task).order_by(Task.created_at.desc()).limit(10).all()
        ctx.update({
            "active_count": active_count,
            "problem_count": problem_count,
            "low_stock_count": low_stock_count,
            "recent_tasks": recent_tasks,
        })
        return templates.TemplateResponse("dashboard/manager.html", ctx)

    elif user.role == "storekeeper":
        new_tasks = db.query(Task).filter(Task.status == "new").order_by(Task.created_at).all()
        my_tasks = db.query(Task).filter(
            Task.assigned_to == user.id, Task.status == "in_progress"
        ).all()
        ctx.update({"new_tasks": new_tasks, "my_tasks": my_tasks})
        return templates.TemplateResponse("dashboard/storekeeper.html", ctx)

    elif user.role == "loader":
        active_tasks = db.query(Task).filter(Task.status == "in_progress").order_by(Task.created_at).all()
        ctx.update({"active_tasks": active_tasks})
        return templates.TemplateResponse("dashboard/loader.html", ctx)

    elif user.role == "accountant":
        from datetime import date
        today_closed = db.query(Task).filter(
            Task.status == "done",
            func.date(Task.closed_at) == date.today()
        ).count()
        ctx.update({"today_closed": today_closed, "today": date.today().isoformat()})
        return templates.TemplateResponse("dashboard/accountant.html", ctx)

    return RedirectResponse("/login", 302)
