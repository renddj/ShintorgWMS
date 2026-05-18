from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from models.address import Zone, Row, Shelf, Level, StorageAddress

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/addresses", response_class=HTMLResponse)
def addresses_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    zones = db.query(Zone).order_by(Zone.name).all()
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    return templates.TemplateResponse("addresses/list.html", {
        "request": request, "user": user, "zones": zones, "addresses": addresses
    })


@router.post("/addresses/zone/new")
def zone_new(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    if not db.query(Zone).filter(Zone.name == name).first():
        db.add(Zone(name=name))
        db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/row/new")
def row_new(request: Request, zone_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    db.add(Row(zone_id=zone_id, name=name))
    db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/shelf/new")
def shelf_new(request: Request, row_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    db.add(Shelf(row_id=row_id, name=name))
    db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/level/new")
def level_new(request: Request, shelf_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    db.add(Level(shelf_id=shelf_id, name=name))
    db.commit()
    return RedirectResponse("/addresses", 302)


@router.post("/addresses/address/new")
def address_new(
    request: Request,
    address_type: str = Form(...),
    zone_id: int = Form(...),
    row_id: int = Form(...),
    shelf_id: int = Form(None),
    level_id: int = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)

    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    row = db.query(Row).filter(Row.id == row_id).first()

    if address_type == "zone_row":
        display = f"Зона {zone.name}, Ряд {row.name}"
        shelf_id = None
        level_id = None
    else:
        shelf = db.query(Shelf).filter(Shelf.id == shelf_id).first()
        level = db.query(Level).filter(Level.id == level_id).first()
        display = f"Зона {zone.name}, Ряд {row.name}, Стеллаж {shelf.name}, Уровень {level.name}"

    addr = StorageAddress(
        address_type=address_type,
        zone_id=zone_id, row_id=row_id,
        shelf_id=shelf_id, level_id=level_id,
        display_name=display,
    )
    db.add(addr)
    db.commit()
    return RedirectResponse("/addresses", 302)


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
