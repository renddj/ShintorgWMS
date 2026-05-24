from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from models.address import Zone, Row, Shelf, Level, StorageAddress
from models.product import StockLocation

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _build_display_name(zone_name, row_name, shelf_name=None, level_name=None):
    if shelf_name and level_name:
        return f"Зона {zone_name}, Ряд {row_name}, Стеллаж {shelf_name}, Уровень {level_name}"
    return f"Зона {zone_name}, Ряд {row_name}"


def _address_has_stock(db, address_id):
    return db.query(StockLocation).filter(
        StockLocation.address_id == address_id,
        StockLocation.quantity > 0,
    ).first() is not None


@router.get("/addresses", response_class=HTMLResponse)
def addresses_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    zones = db.query(Zone).order_by(Zone.name).all()
    return templates.TemplateResponse("addresses/list.html", {
        "request": request, "user": user, "zones": zones
    })


# ── Зоны ─────────────────────────────────────────────────────────────────────

@router.post("/addresses/zone/new")
def zone_new(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    if not db.query(Zone).filter(Zone.name == name).first():
        db.add(Zone(name=name))
        db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/zone/{zone_id}/delete")
def zone_delete(zone_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        return RedirectResponse("/addresses", 302)

    # Проверяем все адреса в зоне
    for row in zone.rows:
        if row.address and _address_has_stock(db, row.address.id):
            return templates.TemplateResponse("addresses/list.html", {
                "request": request, "user": user,
                "zones": db.query(Zone).order_by(Zone.name).all(),
                "error": f"Нельзя удалить зону «{zone.name}» — на адресах есть товар"
            })
        for shelf in row.shelves:
            for level in shelf.levels:
                if level.address and _address_has_stock(db, level.address.id):
                    return templates.TemplateResponse("addresses/list.html", {
                        "request": request, "user": user,
                        "zones": db.query(Zone).order_by(Zone.name).all(),
                        "error": f"Нельзя удалить зону «{zone.name}» — на адресах есть товар"
                    })
    db.delete(zone)
    db.commit()
    return RedirectResponse("/addresses", 302)


# ── Ряды ──────────────────────────────────────────────────────────────────────

@router.post("/addresses/row/new")
def row_new(request: Request, zone_id: int = Form(...), name: str = Form(...),
            db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        return RedirectResponse("/addresses", 302)

    row = Row(zone_id=zone_id, name=name)
    db.add(row)
    db.flush()

    # Ряд без стеллажей = адрес хранения
    addr = StorageAddress(
        row_id=row.id,
        display_name=_build_display_name(zone.name, name)
    )
    db.add(addr)
    db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/row/{row_id}/delete")
def row_delete(row_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    row = db.query(Row).filter(Row.id == row_id).first()
    if not row:
        return RedirectResponse("/addresses", 302)

    # Проверяем остатки
    if row.address and _address_has_stock(db, row.address.id):
        return templates.TemplateResponse("addresses/list.html", {
            "request": request, "user": user,
            "zones": db.query(Zone).order_by(Zone.name).all(),
            "error": f"Нельзя удалить ряд «{row.name}» — на адресе есть товар"
        })
    for shelf in row.shelves:
        for level in shelf.levels:
            if level.address and _address_has_stock(db, level.address.id):
                return templates.TemplateResponse("addresses/list.html", {
                    "request": request, "user": user,
                    "zones": db.query(Zone).order_by(Zone.name).all(),
                    "error": f"Нельзя удалить ряд «{row.name}» — на адресах есть товар"
                })
    db.delete(row)
    db.commit()
    return RedirectResponse("/addresses", 302)


# ── Стеллажи ──────────────────────────────────────────────────────────────────

@router.post("/addresses/shelf/new")
def shelf_new(request: Request, row_id: int = Form(...), name: str = Form(...),
              db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    row = db.query(Row).filter(Row.id == row_id).first()
    if not row:
        return RedirectResponse("/addresses", 302)

    # Нельзя добавить стеллаж если на ряду есть остатки
    if row.address and _address_has_stock(db, row.address.id):
        return templates.TemplateResponse("addresses/list.html", {
            "request": request, "user": user,
            "zones": db.query(Zone).order_by(Zone.name).all(),
            "error": f"Нельзя добавить стеллаж к ряду «{row.name}» — на нём есть товар. Сначала переместите товар."
        })

    # Если у ряда был адрес (без стеллажей) — удаляем его
    if row.address:
        db.delete(row.address)
        db.flush()

    shelf = Shelf(row_id=row_id, name=name)
    db.add(shelf)
    db.commit()

    # Возвращаем JSON с id стеллажа для JS (inline форма уровней)
    return JSONResponse({"shelf_id": shelf.id, "shelf_name": name})


@router.post("/addresses/shelf/{shelf_id}/delete")
def shelf_delete(shelf_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    shelf = db.query(Shelf).filter(Shelf.id == shelf_id).first()
    if not shelf:
        return RedirectResponse("/addresses", 302)

    for level in shelf.levels:
        if level.address and _address_has_stock(db, level.address.id):
            return templates.TemplateResponse("addresses/list.html", {
                "request": request, "user": user,
                "zones": db.query(Zone).order_by(Zone.name).all(),
                "error": f"Нельзя удалить стеллаж «{shelf.name}» — на адресах есть товар"
            })

    row = shelf.row
    db.delete(shelf)
    db.flush()

    # Если у ряда больше нет стеллажей — создаём адрес для ряда
    db.refresh(row)
    if not row.shelves:
        db.add(StorageAddress(
            row_id=row.id,
            display_name=_build_display_name(row.zone.name, row.name)
        ))
    db.commit()
    return RedirectResponse("/addresses", 302)


# ── Уровни ────────────────────────────────────────────────────────────────────

@router.post("/addresses/level/new")
def level_new(request: Request, shelf_id: int = Form(...), name: str = Form(...),
              db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    shelf = db.query(Shelf).filter(Shelf.id == shelf_id).first()
    if not shelf:
        return RedirectResponse("/addresses", 302)

    level = Level(shelf_id=shelf_id, name=name)
    db.add(level)
    db.flush()

    row = shelf.row
    zone = row.zone
    addr = StorageAddress(
        level_id=level.id,
        display_name=_build_display_name(zone.name, row.name, shelf.name, name)
    )
    db.add(addr)
    db.commit()
    return JSONResponse({"level_id": level.id, "level_name": name,
                         "address_id": addr.id, "display_name": addr.display_name})


@router.post("/addresses/level/{level_id}/delete")
def level_delete(level_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    level = db.query(Level).filter(Level.id == level_id).first()
    if not level:
        return RedirectResponse("/addresses", 302)

    if level.address and _address_has_stock(db, level.address.id):
        return templates.TemplateResponse("addresses/list.html", {
            "request": request, "user": user,
            "zones": db.query(Zone).order_by(Zone.name).all(),
            "error": f"Нельзя удалить уровень «{level.name}» — на адресе есть товар"
        })
    db.delete(level)
    db.commit()
    return RedirectResponse("/addresses", 302)


# ── API для каскадных селектов (используется в других местах) ─────────────────

@router.get("/api/rows")
def api_rows(zone_id: int, db: Session = Depends(get_db)):
    rows = db.query(Row).filter(Row.zone_id == zone_id).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/api/shelves")
def api_shelves(row_id: int, db: Session = Depends(get_db)):
    shelves = db.query(Shelf).filter(Shelf.row_id == row_id).all()
    return [{"id": s.id, "name": s.name} for s in shelves]


@router.get("/api/levels")
def api_levels(shelf_id: int, db: Session = Depends(get_db)):
    levels = db.query(Level).filter(Level.shelf_id == shelf_id).all()
    return [{"id": l.id, "name": l.name} for l in levels]
