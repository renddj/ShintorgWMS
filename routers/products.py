import os
import shutil
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.stock_service import receipt, writeoff
from models.product import Product, StockLocation
from models.address import StorageAddress
from config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/products", response_class=HTMLResponse)
def products_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)
    products = db.query(Product).order_by(Product.name).all()
    return templates.TemplateResponse("products/list.html", {
        "request": request, "user": user, "products": products
    })


@router.get("/products/new", response_class=HTMLResponse)
def product_new_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("products/form.html", {
        "request": request, "user": user, "product": None
    })


@router.post("/products/new")
async def product_new(
    request: Request,
    name: str = Form(...),
    article: str = Form(...),
    product_type: str = Form(...),
    unit: str = Form(...),
    tire_size: str = Form(""),
    width: str = Form(""),
    profile: str = Form(""),
    diameter: str = Form(""),
    season: str = Form(""),
    brand: str = Form(""),
    model: str = Form(""),
    tire_type: str = Form(""),
    load_speed_index: str = Form(""),
    min_quantity: float = Form(0),
    comment: str = Form(""),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)

    if db.query(Product).filter(Product.article == article).first():
        return templates.TemplateResponse("products/form.html", {
            "request": request, "user": user, "product": None,
            "error": "Артикул уже существует"
        })

    photo_path = None
    if photo and photo.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        fname = f"product_{article}.{ext}"
        with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/uploads/{fname}"

    p = Product(
        name=name, article=article, product_type=product_type, unit=unit,
        tire_size=tire_size or None, width=width or None, profile=profile or None,
        diameter=diameter or None, season=season or None, brand=brand or None,
        model=model or None, tire_type=tire_type or None,
        load_speed_index=load_speed_index or None,
        min_quantity=min_quantity, comment=comment or None, photo_path=photo_path,
    )
    db.add(p)
    db.commit()
    return RedirectResponse("/products", 302)


@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse("/products", 302)
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    return templates.TemplateResponse("products/detail.html", {
        "request": request, "user": user, "product": product, "addresses": addresses
    })


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def product_edit_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    return templates.TemplateResponse("products/form.html", {
        "request": request, "user": user, "product": product
    })


@router.post("/products/{product_id}/edit")
async def product_edit(
    product_id: int, request: Request,
    name: str = Form(...), article: str = Form(...),
    product_type: str = Form(...), unit: str = Form(...),
    tire_size: str = Form(""), width: str = Form(""), profile: str = Form(""),
    diameter: str = Form(""), season: str = Form(""), brand: str = Form(""),
    model: str = Form(""), tire_type: str = Form(""), load_speed_index: str = Form(""),
    min_quantity: float = Form(0), comment: str = Form(""),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse("/products", 302)

    if photo and photo.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        fname = f"product_{article}.{ext}"
        with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
            shutil.copyfileobj(photo.file, f)
        product.photo_path = f"/uploads/{fname}"

    product.name = name
    product.article = article
    product.product_type = product_type
    product.unit = unit
    product.tire_size = tire_size or None
    product.width = width or None
    product.profile = profile or None
    product.diameter = diameter or None
    product.season = season or None
    product.brand = brand or None
    product.model = model or None
    product.tire_type = tire_type or None
    product.load_speed_index = load_speed_index or None
    product.min_quantity = min_quantity
    product.comment = comment or None
    db.commit()
    return RedirectResponse(f"/products/{product_id}", 302)


@router.post("/products/{product_id}/delete")
def product_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse("/products", 302)


@router.post("/products/{product_id}/receipt")
def product_receipt(
    product_id: int, request: Request,
    address_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "storekeeper"):
        return RedirectResponse("/dashboard", 302)
    _, error = receipt(db, product_id, address_id, quantity, user.id, comment or None)
    if error:
        product = db.query(Product).filter(Product.id == product_id).first()
        addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
        return templates.TemplateResponse("products/detail.html", {
            "request": request, "user": user, "product": product,
            "addresses": addresses, "error": error
        })
    return RedirectResponse(f"/products/{product_id}", 302)


@router.post("/products/{product_id}/writeoff")
def product_writeoff(
    product_id: int, request: Request,
    address_id: int = Form(...),
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ("admin", "storekeeper"):
        return RedirectResponse("/dashboard", 302)
    _, error = writeoff(db, product_id, address_id, quantity, user.id, comment or None)
    if error:
        product = db.query(Product).filter(Product.id == product_id).first()
        addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
        return templates.TemplateResponse("products/detail.html", {
            "request": request, "user": user, "product": product,
            "addresses": addresses, "error": error
        })
    return RedirectResponse(f"/products/{product_id}", 302)
