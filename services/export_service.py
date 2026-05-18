from datetime import date
from io import BytesIO
import openpyxl
from sqlalchemy.orm import Session
from models.task import Task
from models.stock_operation import StockOperation


def generate_excel(db: Session, date_from: date, date_to: date, op_type: str = "all") -> BytesIO:
    wb = openpyxl.Workbook()

    # Sheet: Отгрузки
    if op_type in ("all", "shipment"):
        ws1 = wb.active
        ws1.title = "Отгрузки"
        headers = ["№ задания", "Дата закрытия", "Наименование товара", "Артикул", "Количество", "Ед. изм.", "Кладовщик"]
        ws1.append(headers)

        tasks = db.query(Task).filter(
            Task.status == "done",
            Task.closed_at >= date_from,
            Task.closed_at <= date_to,
        ).all()

        for task in tasks:
            ws1.append([
                task.id,
                task.closed_at.strftime("%d.%m.%Y %H:%M") if task.closed_at else "",
                task.product.name if task.product else "",
                task.product.article if task.product else "",
                float(task.quantity),
                task.product.unit if task.product else "",
                task.assignee.full_name if task.assignee else "",
            ])
    else:
        ws1 = wb.active
        ws1.title = "Отгрузки"

    # Sheet: Приёмки
    if op_type in ("all", "receipt"):
        ws2 = wb.create_sheet("Приёмки")
        headers2 = ["Дата", "Наименование товара", "Артикул", "Количество", "Комментарий"]
        ws2.append(headers2)

        ops = db.query(StockOperation).filter(
            StockOperation.operation == "receipt",
            StockOperation.created_at >= date_from,
            StockOperation.created_at <= date_to,
        ).all()

        for op in ops:
            ws2.append([
                op.created_at.strftime("%d.%m.%Y %H:%M") if op.created_at else "",
                op.product.name if op.product else "",
                op.product.article if op.product else "",
                float(op.quantity),
                op.comment or "",
            ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
