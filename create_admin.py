#!/usr/bin/env python3
"""Script to create first admin user. Run once after first deploy."""
import sys
import os

# Fix encoding on Windows
if sys.platform == "win32":
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
import models  # noqa: F401
from models.user import User
from services.auth_service import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def safe_input(prompt):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    line = sys.stdin.buffer.readline()
    return line.decode('utf-8', errors='replace').rstrip('\n').rstrip('\r')


username = safe_input("Логин администратора [admin]: ").strip() or "admin"
full_name = safe_input("ФИО администратора [Администратор]: ").strip() or "Администратор"

# Sanitize — remove surrogate characters
username = username.encode('utf-8', 'ignore').decode('utf-8')
full_name = full_name.encode('utf-8', 'ignore').decode('utf-8')

while True:
    password = safe_input("Пароль (минимум 8 символов): ").strip()
    if len(password) >= 8:
        break
    print("Пароль слишком короткий!")

existing = db.query(User).filter(User.username == username).first()
if existing:
    print(f"Пользователь '{username}' уже существует.")
    db.close()
    sys.exit(0)

admin = User(
    username=username,
    full_name=full_name,
    role="admin",
    password_hash=hash_password(password),
    is_active=True,
)
db.add(admin)
db.commit()
print(f"\nАдминистратор '{username}' создан успешно.")
db.close()