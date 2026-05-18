import os
import shutil
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user, require_roles
from services.stock_service import receipt, writeoff
from models.product import Product
from models.address import StorageAddress
from config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ALLOWED_ROLES_VIEW = ["admin", "manager", "storekeeper", "loader", "accountant"]
ALLOWED_ROLES_EDIT = ["admin"]


@router.get("/products", response_class=HTMLResponse)
def products_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", 302)
    if user.role not in ALLOWED_ROLES_VIEW:
        return RedirectResponse("/dashboard", 302)
    products = db.query(Product).order_by(Product.name).all()
    return templates.TemplateResponse("products/list.html", {"request": request, "user": user, "products": products})


@router.get("/products/new", response_class=HTMLResponse)
def product_new_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED_ROLES_EDIT:
        return RedirectResponse("/dashboard", 302)
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    return templates.TemplateResponse("products/form.html", {"request": request, "user": user, "addresses": addresses, "product": None})


@router.post("/products/new")
async def product_new(
    request: Request,
    name: str = Form(...),
    article: str = Form(...),
    product_type: str = Form(...),
    unit: str = Form(...),
    address_id: int = Form(...),
    min_quantity: float = Form(0),
    comment: str = Form(""),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED_ROLES_EDIT:
        return RedirectResponse("/dashboard", 302)

    photo_path = None
    if photo and photo.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        fname = f"product_{article}.{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        with open(fpath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/uploads/{fname}"

    existing = db.query(Product).filter(Product.article == article).first()
    if existing:
        addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
        return templates.TemplateResponse("products/form.html", {
            "request": request, "user": user, "addresses": addresses,
            "product": None, "error": "Артикул уже существует"
        })

    p = Product(
        name=name, article=article, product_type=product_type, unit=unit,
        address_id=address_id, min_quantity=min_quantity,
        comment=comment or None, photo_path=photo_path,
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
    return templates.TemplateResponse("products/detail.html", {"request": request, "user": user, "product": product})


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def product_edit_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED_ROLES_EDIT:
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    addresses = db.query(StorageAddress).order_by(StorageAddress.display_name).all()
    return templates.TemplateResponse("products/form.html", {"request": request, "user": user, "product": product, "addresses": addresses})


@router.post("/products/{product_id}/edit")
async def product_edit(
    product_id: int,
    request: Request,
    name: str = Form(...),
    article: str = Form(...),
    product_type: str = Form(...),
    unit: str = Form(...),
    address_id: int = Form(...),
    min_quantity: float = Form(0),
    comment: str = Form(""),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED_ROLES_EDIT:
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse("/products", 302)

    if photo and photo.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        fname = f"product_{article}.{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        with open(fpath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        product.photo_path = f"/uploads/{fname}"

    product.name = name
    product.article = article
    product.product_type = product_type
    product.unit = unit
    product.address_id = address_id
    product.min_quantity = min_quantity
    product.comment = comment or None
    db.commit()
    return RedirectResponse(f"/products/{product_id}", 302)


@router.post("/products/{product_id}/delete")
def product_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED_ROLES_EDIT:
        return RedirectResponse("/dashboard", 302)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse("/products", 302)


@router.post("/products/{product_id}/receipt")
def product_receipt(
    product_id: int, request: Request,
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    receipt(db, product_id, quantity, user.id, comment or None)
    return RedirectResponse(f"/products/{product_id}", 302)


@router.post("/products/{product_id}/writeoff")
def product_writeoff(
    product_id: int, request: Request,
    quantity: float = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", 302)
    result, error = writeoff(db, product_id, quantity, user.id, comment or None)
    if error:
        product = db.query(Product).filter(Product.id == product_id).first()
        return templates.TemplateResponse("products/detail.html", {
            "request": request, "user": user, "product": product, "error": error
        })
    return RedirectResponse(f"/products/{product_id}", 302)
