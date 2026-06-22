

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