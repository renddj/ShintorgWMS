from sqlalchemy.orm import Session
from models.product import Product, StockLocation
from models.stock_operation import StockOperation


def _get_or_create_location(db, product_id, address_id):
    loc = db.query(StockLocation).filter(
        StockLocation.product_id == product_id,
        StockLocation.address_id == address_id,
    ).with_for_update().first()
    if not loc:
        loc = StockLocation(product_id=product_id, address_id=address_id, quantity=0, reserved_quantity=0)
        db.add(loc)
        db.flush()
    return loc


def receipt(db: Session, product_id: int, address_id: int, quantity: float, user_id: int, comment: str = None):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None, "Товар не найден"

    loc = _get_or_create_location(db, product_id, address_id)
    qty_before = float(loc.quantity or 0)
    loc.quantity = qty_before + quantity

    op = StockOperation(
        product_id=product_id,
        operation="receipt",
        quantity=quantity,
        qty_before=qty_before,
        qty_after=float(loc.quantity),
        performed_by=user_id,
        comment=comment,
    )
    db.add(op)
    db.commit()
    return product, None


def writeoff(db: Session, product_id: int, address_id: int, quantity: float, user_id: int, comment: str = None):
    loc = db.query(StockLocation).filter(
        StockLocation.product_id == product_id,
        StockLocation.address_id == address_id,
    ).with_for_update().first()

    if not loc:
        return None, "На этом адресе нет товара"

    available = float(loc.quantity or 0) - float(loc.reserved_quantity or 0)
    if available < quantity:
        return None, f"Недостаточно товара на адресе. Доступно: {available}"

    qty_before = float(loc.quantity)
    loc.quantity = qty_before - quantity

    op = StockOperation(
        product_id=product_id,
        operation="writeoff",
        quantity=quantity,
        qty_before=qty_before,
        qty_after=float(loc.quantity),
        performed_by=user_id,
        comment=comment,
    )
    db.add(op)
    db.commit()
    return loc, None
