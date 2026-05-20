# from datetime import date
# from fastapi import APIRouter, Request, Depends
# from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
# from fastapi.templating import Jinja2Templates
# from sqlalchemy.orm import Session
# from database import get_db
# from services.auth_service import get_current_user
# from services.export_service import generate_excel

# router = APIRouter()
# templates = Jinja2Templates(directory="templates")


# @router.get("/export", response_class=HTMLResponse)
# def export_page(request: Request, db: Session = Depends(get_db)):
#     user = get_current_user(request, db)
#     if not user or user.role not in ("admin", "accountant"):
#         return RedirectResponse("/dashboard", 302)
#     return templates.TemplateResponse("export/index.html", {
#         "request": request, "user": user,
#         "today": date.today().isoformat()
#     })


# @router.get("/export/download")
# def export_download(
#     request: Request,
#     date_from: str,
#     date_to: str,
#     op_type: str = "all",
#     db: Session = Depends(get_db),
# ):
#     user = get_current_user(request, db)
#     if not user or user.role not in ("admin", "accountant"):
#         return RedirectResponse("/dashboard", 302)

#     d_from = date.fromisoformat(date_from)
#     d_to = date.fromisoformat(date_to)
#     buf = generate_excel(db, d_from, d_to, op_type)

#     filename = f"shintorg_{date_from}_{date_to}.xlsx"
#     return StreamingResponse(
#         buf,
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers={"Content-Disposition": f"attachment; filename={filename}"},
#     )

# from datetime import date
# from fastapi import APIRouter, Request, Depends
# from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
# from fastapi.templating import Jinja2Templates
# from sqlalchemy.orm import Session
# from database import get_db
# from services.auth_service import get_current_user
# from services.export_service import generate_excel, generate_csv

# router = APIRouter()
# templates = Jinja2Templates(directory="templates")

# ALLOWED = ["admin", "accountant"]


# @router.get("/export", response_class=HTMLResponse)
# def export_page(request: Request, db: Session = Depends(get_db)):
#     user = get_current_user(request, db)
#     if not user or user.role not in ALLOWED:
#         return RedirectResponse("/dashboard", 302)
#     return templates.TemplateResponse("export/index.html", {
#         "request": request, "user": user,
#         "today": date.today().isoformat()
#     })


# @router.get("/export/download")
# def export_download(
#     request: Request,
#     date_from: str,
#     date_to: str,
#     op_type: str = "all",
#     fmt: str = "xlsx",
#     db: Session = Depends(get_db),
# ):
#     user = get_current_user(request, db)
#     if not user or user.role not in ALLOWED:
#         return RedirectResponse("/dashboard", 302)

#     d_from = date.fromisoformat(date_from)
#     d_to = date.fromisoformat(date_to)

#     if fmt == "csv":
#         buf = generate_csv(db, d_from, d_to, op_type)
#         filename = f"shintorg_{date_from}_{date_to}.csv"
#         media_type = "text/csv; charset=utf-8"
#     else:
#         buf = generate_excel(db, d_from, d_to, op_type)
#         filename = f"shintorg_{date_from}_{date_to}.xlsx"
#         media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

#     return StreamingResponse(
#         buf,
#         media_type=media_type,
#         headers={"Content-Disposition": f"attachment; filename={filename}"},
#     )


# @router.get("/export/debug")
# def export_debug(request: Request, db: Session = Depends(get_db)):
#     from models.task import Task
#     from models.stock_operation import StockOperation
#     from datetime import datetime, time

#     tasks_done = db.query(Task).filter(Task.status == "done").all()
#     ops_receipt = db.query(StockOperation).filter(StockOperation.operation == "receipt").all()

#     result = {
#         "tasks_done": [
#             {
#                 "id": t.id,
#                 "closed_at": str(t.closed_at),
#                 "product": t.product.name if t.product else None,
#                 "assignee": t.assignee.full_name if t.assignee else None,
#             }
#             for t in tasks_done
#         ],
#         "receipts": [
#             {
#                 "id": o.id,
#                 "created_at": str(o.created_at),
#                 "product": o.product.name if o.product else None,
#                 "quantity": float(o.quantity),
#             }
#             for o in ops_receipt
#         ],
#     }
#     from fastapi.responses import JSONResponse
#     return JSONResponse(result)


# @router.get("/export/debug")
# def export_debug(request: Request, db: Session = Depends(get_db)):
#     from models.task import Task
#     from models.stock_operation import StockOperation
#     from sqlalchemy import cast, Date
#     import datetime

#     tasks_done = db.query(Task).filter(Task.status == "done").all()
#     receipts = db.query(StockOperation).filter(StockOperation.operation == "receipt").all()

#     result = {
#         "tasks_done": [
#             {
#                 "id": t.id,
#                 "closed_at": str(t.closed_at),
#                 "closed_at_type": type(t.closed_at).__name__,
#                 "product": t.product.name if t.product else None,
#             }
#             for t in tasks_done
#         ],
#         "receipts": [
#             {
#                 "id": r.id,
#                 "created_at": str(r.created_at),
#                 "product": r.product.name if r.product else None,
#                 "qty": float(r.quantity),
#             }
#             for r in receipts
#         ],
#         "today": str(datetime.date.today()),
#     }
#     return result

from datetime import date
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from services.export_service import generate_excel, generate_csv

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ALLOWED = ["admin", "accountant"]


@router.get("/export", response_class=HTMLResponse)
def export_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED:
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("export/index.html", {
        "request": request, "user": user,
        "today": date.today().isoformat()
    })


@router.get("/export/download")
def export_download(
    request: Request,
    date_from: str,
    date_to: str,
    op_type: str = "all",
    fmt: str = "xlsx",
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in ALLOWED:
        return RedirectResponse("/dashboard", 302)

    d_from = date.fromisoformat(date_from)
    d_to = date.fromisoformat(date_to)

    if fmt == "csv":
        buf = generate_csv(db, d_from, d_to, op_type)
        filename = f"shintorg_{date_from}_{date_to}.csv"
        media_type = "text/csv; charset=utf-8"
    else:
        buf = generate_excel(db, d_from, d_to, op_type)
        filename = f"shintorg_{date_from}_{date_to}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        buf,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )