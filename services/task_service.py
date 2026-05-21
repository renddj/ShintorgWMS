from datetime import datetime
from sqlalchemy.orm import Session
from models.task import Task, TaskLine
from models.product import Product, StockLocation
from models.stock_operation import StockOperation


# ── Создание задания (отгрузка или приёмка) ──────────────────────────────────

def create_task(db: Session, task_type: str, product_id: int, quantity: float,
                created_by: int, comment: str = None):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None, "Товар не найден"

    if task_type == "shipment":
        available = product.available_quantity
        if available < quantity:
            return None, f"Недостаточно товара. Доступно: {available} {product.unit}"

    task = Task(
        task_type=task_type,
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


# ── Планирование (кладовщик указывает строки) ────────────────────────────────

def plan_task(db: Session, task_id: int, user_id: int, lines: list[dict]):
    """lines = [{"address_id": int, "quantity": float}, ...]"""
    task = db.query(Task).filter(Task.id == task_id, Task.status == "new").with_for_update().first()
    if not task:
        return None, "Задание не найдено или уже в работе"

    total = sum(float(l["quantity"]) for l in lines if float(l["quantity"]) > 0)
    if abs(total - float(task.quantity)) > 0.001:
        return None, f"Сумма строк ({total}) не совпадает с количеством задания ({float(task.quantity)})"

    # Для отгрузки — резервируем остатки по адресам
    if task.task_type == "shipment":
        for l in lines:
            qty = float(l["quantity"])
            if qty <= 0:
                continue
            loc = db.query(StockLocation).filter(
                StockLocation.product_id == task.product_id,
                StockLocation.address_id == l["address_id"],
            ).with_for_update().first()
            if not loc:
                return None, f"На адресе {l['address_id']} нет товара"
            available = float(loc.quantity or 0) - float(loc.reserved_quantity or 0)
            if available < qty:
                return None, f"Недостаточно товара на адресе. Доступно: {available}"
            loc.reserved_quantity = float(loc.reserved_quantity or 0) + qty

    # Сохраняем строки
    for l in lines:
        qty = float(l["quantity"])
        if qty <= 0:
            continue
        db.add(TaskLine(task_id=task.id, address_id=l["address_id"], quantity=qty))

    task.status = "in_progress"
    task.assigned_to = user_id
    db.commit()
    db.refresh(task)
    return task, None


# ── Закрытие задания ──────────────────────────────────────────────────────────

def close_task(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.status == "in_progress").with_for_update().first()
    if not task:
        return None, "Задание не найдено или не в работе"

    for line in task.lines:
        qty = float(line.quantity)
        loc = db.query(StockLocation).filter(
            StockLocation.product_id == task.product_id,
            StockLocation.address_id == line.address_id,
        ).with_for_update().first()

        if task.task_type == "shipment":
            qty_before = float(loc.quantity)
            loc.quantity = qty_before - qty
            loc.reserved_quantity = max(0, float(loc.reserved_quantity or 0) - qty)
            op_type = "shipment"
            op_comment = f"Отгрузка по заданию #{task.id}"
        else:
            # receipt — создаём локацию если нет
            if not loc:
                loc = StockLocation(
                    product_id=task.product_id,
                    address_id=line.address_id,
                    quantity=0, reserved_quantity=0,
                )
                db.add(loc)
                db.flush()
            qty_before = float(loc.quantity)
            loc.quantity = qty_before + qty
            op_type = "receipt"
            op_comment = f"Приёмка по заданию #{task.id}"

        db.add(StockOperation(
            product_id=task.product_id,
            operation=op_type,
            quantity=qty,
            qty_before=qty_before,
            qty_after=float(loc.quantity),
            task_id=task.id,
            performed_by=user_id,
            comment=op_comment,
        ))

    task.status = "done"
    task.assigned_to = user_id
    task.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task, None


# ── Проблема ─────────────────────────────────────────────────────────────────

def report_problem(db: Session, task_id: int, user_id: int, problem_comment: str):
    task = db.query(Task).filter(Task.id == task_id, Task.status == "in_progress").with_for_update().first()
    if not task:
        return None, "Задание не найдено или не в работе"

    # Снять резервы для отгрузки
    if task.task_type == "shipment":
        for line in task.lines:
            loc = db.query(StockLocation).filter(
                StockLocation.product_id == task.product_id,
                StockLocation.address_id == line.address_id,
            ).with_for_update().first()
            if loc:
                loc.reserved_quantity = max(0, float(loc.reserved_quantity or 0) - float(line.quantity))

    task.status = "problem"
    task.problem_comment = problem_comment
    db.commit()
    db.refresh(task)
    return task, None


# ── Отмена ───────────────────────────────────────────────────────────────────

def cancel_task(db: Session, task_id: int):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.status.in_(["new", "problem"])
    ).with_for_update().first()
    if not task:
        return None, "Задание нельзя отменить"

    # Снять резервы если были строки (статус problem — строки уже сняты в report_problem)
    if task.status == "new" and task.task_type == "shipment":
        for line in task.lines:
            loc = db.query(StockLocation).filter(
                StockLocation.product_id == task.product_id,
                StockLocation.address_id == line.address_id,
            ).with_for_update().first()
            if loc:
                loc.reserved_quantity = max(0, float(loc.reserved_quantity or 0) - float(line.quantity))

    task.status = "cancelled"
    db.commit()
    db.refresh(task)
    return task, None
