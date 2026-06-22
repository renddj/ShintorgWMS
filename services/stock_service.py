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


def move(db: Session, product_id: int, from_address_id: int, to_address_id: int,
         quantity: float, user_id: int, comment: str = None):
    if from_address_id == to_address_id:
        return None, "Адрес источника и назначения совпадают"

    from_loc = db.query(StockLocation).filter(
        StockLocation.product_id == product_id,
        StockLocation.address_id == from_address_id,
    ).with_for_update().first()

    if not from_loc:
        return None, "На адресе источника нет этого товара"

    available = float(from_loc.quantity or 0) - float(from_loc.reserved_quantity or 0)
    if available < quantity:
        return None, f"Недостаточно товара. Доступно: {available}"

    qty_before_from = float(from_loc.quantity)
    from_loc.quantity = qty_before_from - quantity

    to_loc = db.query(StockLocation).filter(
        StockLocation.product_id == product_id,
        StockLocation.address_id == to_address_id,
    ).with_for_update().first()

    if not to_loc:
        to_loc = StockLocation(
            product_id=product_id,
            address_id=to_address_id,
            quantity=0, reserved_quantity=0,
        )
        db.add(to_loc)
        db.flush()

    qty_before_to = float(to_loc.quantity)
    to_loc.quantity = qty_before_to + quantity

    from models.address import StorageAddress as _SA
    from_addr = db.query(_SA).filter_by(id=from_address_id).first()
    to_addr = db.query(_SA).filter_by(id=to_address_id).first()
    from_name = from_addr.display_name if from_addr else str(from_address_id)
    to_name = to_addr.display_name if to_addr else str(to_address_id)

    db.add(StockOperation(
        product_id=product_id, operation="move_out",
        quantity=quantity, qty_before=qty_before_from, qty_after=float(from_loc.quantity),
        performed_by=user_id,
        comment=f"Перемещение → {to_name}" + (f". {comment}" if comment else ""),
    ))
    db.add(StockOperation(
        product_id=product_id, operation="move_in",
        quantity=quantity, qty_before=qty_before_to, qty_after=float(to_loc.quantity),
        performed_by=user_id,
        comment=f"Перемещение ← {from_name}" + (f". {comment}" if comment else ""),
    ))

    db.commit()
    return True, None
