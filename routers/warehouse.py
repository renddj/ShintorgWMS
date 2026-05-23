from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.stock_service import move, receipt
from services.task_service import create_task
from models.product import Product, StockLocation
from models.address import StorageAddress, Zone

router = APIRouter()
templates = Jinja2Templates(directory="templates")

VIEW_ROLES = ["admin", "manager", "storekeeper", "accountant"]
EDIT_ROLES = ["admin", "storekeeper"]


def _build_address_rows(db):
    """
    Возвращает список строк для таблицы сгруппированных по адресу.
    Каждый элемент: {
        "address": StorageAddress,
        "rowspan": int,
        "locations": [StockLocation, ...],  # может быть пустым
    }
    """
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    locations = db.query(StockLocation).filter(StockLocation.quantity > 0).all()

    # Группируем локации по address_id
    loc_by_addr = {}
    for loc in locations:
        loc_by_addr.setdefault(loc.address_id, []).append(loc)

    rows = []
    for addr in addresses:
        locs = loc_by_addr.get(addr.id, [])
        rows.append({
            "address": addr,
            "rowspan": max(len(locs), 1),
            "locations": locs,
        })
    return rows


def _get_context(db):
    return {
        "address_rows": _build_address_rows(db),
        "zones": db.query(Zone).order_by(Zone.name).all(),
        "products": db.query(Product).order_by(Product.name).all(),
        "addresses": db.query(StorageAddress).order_by(StorageAddress.display_name).all(),
    }


@router.get("/warehouse", response_class=HTMLResponse)
def warehouse_map(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in VIEW_ROLES:
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("warehouse/map.html", {
        "request": request, "user": user, **_get_context(db)
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

    if from_address_id == to_address_id:
        error = "Адрес источника и назначения совпадают"
    else:
        _, error = move(db, product_id, from_address_id, to_address_id, quantity, user.id, comment or None)

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request, "user": user,
        "error": error,
        "success": None if error else "Перемещение выполнено",
        **_get_context(db),
    })


@router.post("/warehouse/task")
def warehouse_task(
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

    if from_address_id == to_address_id:
        return templates.TemplateResponse("warehouse/map.html", {
            "request": request, "user": user,
            "error": "Адрес источника и назначения совпадают",
            **_get_context(db),
        })

    task, error = create_task(db, "move", product_id, quantity, user.id, comment or None, to_address_id)

    # Сразу создаём task_line с адресом источника и переводим в in_progress
    if task and not error:
        from models.task import TaskLine
        from models.product import StockLocation
        loc = db.query(StockLocation).filter(
            StockLocation.product_id == product_id,
            StockLocation.address_id == from_address_id,
        ).with_for_update().first()
        if loc:
            available = float(loc.quantity or 0) - float(loc.reserved_quantity or 0)
            if available >= quantity:
                loc.reserved_quantity = float(loc.reserved_quantity or 0) + quantity
                db.add(TaskLine(task_id=task.id, address_id=from_address_id, quantity=quantity))
                task.status = "in_progress"
                task.assigned_to = user.id
                db.commit()
            else:
                error = f"Недостаточно товара на адресе. Доступно: {available}"
                task.status = "cancelled"
                db.commit()

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request, "user": user,
        "error": error,
        "success": None if error else f"Задание #{task.id} на перемещение создано",
        **_get_context(db),
    })


@router.post("/warehouse/receipt")
def warehouse_receipt(
    request: Request,
    product_id: int = Form(...),
    address_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)

    _, error = receipt(db, product_id, address_id, quantity, user.id, comment or None)

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request, "user": user,
        "error": error,
        "success": None if error else "Товар принят на склад",
        **_get_context(db),
    })


@router.post("/warehouse/writeoff")
def warehouse_writeoff(
    request: Request,
    product_id: int = Form(...),
    from_address_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    from services.stock_service import writeoff
    user = get_current_user(request, db)
    if not user or user.role not in EDIT_ROLES:
        return RedirectResponse("/dashboard", 302)

    _, error = writeoff(db, product_id, from_address_id, quantity, user.id, comment or None)

    return templates.TemplateResponse("warehouse/map.html", {
        "request": request, "user": user,
        "error": error,
        "success": None if error else "Товар списан",
        **_get_context(db),
    })