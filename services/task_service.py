from datetime import datetime
from sqlalchemy.orm import Session
from models.task import Task
from models.product import Product
from models.stock_operation import StockOperation


def create_task(db: Session, product_id: int, quantity: float, created_by: int, comment: str = None):
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        return None, "Товар не найден"

    available = float(product.quantity or 0) - float(product.reserved_quantity or 0)
    if available < quantity:
        return None, f"Недостаточно товара. Доступно: {available} {product.unit}"

    product.reserved_quantity = float(product.reserved_quantity or 0) + quantity

    task = Task(
        product_id=product_id,
        quantity=quantity,
        status="new",
        created_by=created_by,
        comment=comment,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task, None


def take_task(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.status == "new").with_for_update().first()
    if not task:
        return None, "Задание не найдено или уже взято"
    task.status = "in_progress"
    task.assigned_to = user_id
    db.commit()
    db.refresh(task)
    return task, None


def close_task(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.status == "in_progress").with_for_update().first()
    if not task:
        return None, "Задание не найдено или не в работе"

    product = db.query(Product).filter(Product.id == task.product_id).with_for_update().first()
    qty_before = float(product.quantity or 0)
    qty_after = qty_before - float(task.quantity)

    product.quantity = qty_after
    product.reserved_quantity = max(0, float(product.reserved_quantity or 0) - float(task.quantity))

    op = StockOperation(
        product_id=product.id,
        operation="shipment",
        quantity=float(task.quantity),
        qty_before=qty_before,
        qty_after=qty_after,
        task_id=task.id,
        performed_by=user_id,
        comment=f"Отгрузка по заданию #{task.id}",
    )
    db.add(op)

    task.status = "done"
    task.assigned_to = user_id
    task.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task, None


def report_problem(db: Session, task_id: int, user_id: int, problem_comment: str):
    task = db.query(Task).filter(Task.id == task_id, Task.status == "in_progress").with_for_update().first()
    if not task:
        return None, "Задание не найдено или не в работе"

    product = db.query(Product).filter(Product.id == task.product_id).with_for_update().first()
    product.reserved_quantity = max(0, float(product.reserved_quantity or 0) - float(task.quantity))

    task.status = "problem"
    task.problem_comment = problem_comment
    db.commit()
    db.refresh(task)
    return task, None


def cancel_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.status.in_(["new", "problem"])).with_for_update().first()
    if not task:
        return None, "Задание нельзя отменить"

    if task.status == "new":
        product = db.query(Product).filter(Product.id == task.product_id).with_for_update().first()
        product.reserved_quantity = max(0, float(product.reserved_quantity or 0) - float(task.quantity))

    task.status = "cancelled"
    db.commit()
    db.refresh(task)
    return task, None
