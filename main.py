from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from database import engine, Base
import models  # noqa: F401 — register all models

from routers import auth, dashboard, products, addresses, tasks, stock, export, users, warehouse

app = FastAPI(title="Шинторг WMS")

# Create tables on startup (for dev; use alembic in prod)
Base.metadata.create_all(bind=engine)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Uploads directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(addresses.router)
app.include_router(tasks.router)
app.include_router(stock.router)
app.include_router(export.router)
app.include_router(users.router)
app.include_router(warehouse.router)


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
