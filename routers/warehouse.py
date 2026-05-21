from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.stock_service import move
from models.product import Product, StockLocation
from models.address import StorageAddress, Zone

router = APIRouter()
templates = Jinja2Templates(directory="templates")

VIEW_ROLES = ["admin", "manager", "storekeeper", "accountant"]
EDIT_ROLES = ["admin", "storekeeper"]


@router.get("/warehouse", response_class=HTMLResponse)
def warehouse_map(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in VIEW_ROLES:
        return RedirectResponse("/dashboard", 302)

    # Все локации с ненулевым остатком + адреса
    locations = db.query(StockLocation).filter(StockLocation.quantity > 0).all()
    zones = db.query(Zone).order_by(Zone.name).all()
    products = db.query(Product).order_by(Product.name).all()
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request,
        "user": user,
        "locations": locations,
        "zones": zones,
        "products": products,
        "addresses": addresses,
    })


@router.post("/warehouse/move")
def warehouse_move(
    request: Request,
    product_id: int = Form(...),
    from_address_id: int = Form(...),
    to_address_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in EDIT_ROLES:
        return RedirectResponse("/dashboard", 302)

    _, error = move(db, product_id, from_address_id, to_address_id, quantity, user.id, comment or None)

    locations = db.query(StockLocation).filter(StockLocation.quantity > 0).all()
    zones = db.query(Zone).order_by(Zone.name).all()
    products = db.query(Product).order_by(Product.name).all()
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request,
        "user": user,
        "locations": locations,
        "zones": zones,
        "products": products,
        "addresses": addresses,
        "error": error,
        "success": None if error else "Перемещение выполнено успешно",
    })
