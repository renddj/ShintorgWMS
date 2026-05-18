from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from models.stock_operation import StockOperation

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/stock/history", response_class=HTMLResponse)
def stock_history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "accountant"):
        return RedirectResponse("/dashboard", 302)
    ops = db.query(StockOperation).order_by(StockOperation.created_at.desc()).limit(200).all()
    return templates.TemplateResponse("stock/history.html", {"request": request, "user": user, "ops": ops})
