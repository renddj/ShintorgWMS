from sqlalchemy.orm import Session
from models.product import Product
from models.stock_operation import StockOperation


def receipt(db: Session, product_id: int, quantity: float, user_id: int, comment: str = None):
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        return None, "Товар не найден"

    qty_before = float(product.quantity or 0)
    qty_after = qty_before + quantity
    product.quantity = qty_after

    op = StockOperation(
        product_id=product_id,
        operation="receipt",
        quantity=quantity,
        qty_before=qty_before,
        qty_after=qty_after,
        performed_by=user_id,
        comment=comment,
    )
    db.add(op)
    db.commit()
    return product, None


def writeoff(db: Session, product_id: int, quantity: float, user_id: int, comment: str = None):
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        return None, "Товар не найден"

    available = float(product.quantity or 0) - float(product.reserved_quantity or 0)
    if available < quantity:
        return None, f"Недостаточно товара для списания. Доступно: {available}"

    qty_before = float(product.quantity or 0)
    qty_after = qty_before - quantity
    product.quantity = qty_after

    op = StockOperation(
        product_id=product_id,
        operation="writeoff",
        quantity=quantity,
        qty_before=qty_before,
        qty_after=qty_after,
        performed_by=user_id,
        comment=comment,
    )
    db.add(op)
    db.commit()
    return product, None
