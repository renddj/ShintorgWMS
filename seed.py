#!/usr/bin/env python3
"""
Скрипт заполнения базы данных тестовыми данными.
Запуск: docker compose exec app python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
import models  # noqa
from models.user import User
from models.address import Zone, Row, Shelf, Level, StorageAddress
from models.product import Product, StockLocation
from models.stock_operation import StockOperation
from services.auth_service import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("Очистка базы данных...")
db.query(StockOperation).delete()
db.query(StockLocation).delete()
db.query(StorageAddress).delete()
db.query(Level).delete()
db.query(Shelf).delete()
db.query(Row).delete()
db.query(Zone).delete()
db.query(Product).delete()
db.query(User).delete()
db.commit()

# ── Пользователи ─────────────────────────────────────────────────────────────
print("Создание пользователей...")

users_data = [
    ("admin",      "Иванов Иван Иванович",     "admin"),
    ("manager1",   "Петрова Анна Сергеевна",   "manager"),
    ("store1",     "Сидоров Алексей Петрович",  "storekeeper"),
    ("store2",     "Козлова Мария Владимировна","storekeeper"),
    ("loader1",    "Новиков Дмитрий Олегович",  "loader"),
    ("loader2",    "Соколов Андрей Николаевич", "loader"),
    ("accountant1","Морозова Елена Игоревна",   "accountant"),
]

user_objs = {}
for username, full_name, role in users_data:
    u = User(username=username, full_name=full_name, role=role,
             password_hash=hash_password("12345678"), is_active=True)
    db.add(u)
    user_objs[username] = u

db.commit()
print(f"  Создано {len(users_data)} пользователей (пароль для всех: 12345678)")

# ── Адресная структура ────────────────────────────────────────────────────────
print("Создание адресной структуры...")

def make_addr(display_name, row_id=None, level_id=None):
    a = StorageAddress(display_name=display_name, row_id=row_id, level_id=level_id)
    db.add(a)
    db.flush()
    return a

# Зона А — крупногабаритные, только ряды
zone_a = Zone(name="А")
db.add(zone_a)
db.flush()

row_a1 = Row(zone_id=zone_a.id, name="А1")
row_a2 = Row(zone_id=zone_a.id, name="А2")
row_a3 = Row(zone_id=zone_a.id, name="А3")
db.add_all([row_a1, row_a2, row_a3])
db.flush()

addr_a1 = make_addr("Зона А, Ряд А1", row_id=row_a1.id)
addr_a2 = make_addr("Зона А, Ряд А2", row_id=row_a2.id)
addr_a3 = make_addr("Зона А, Ряд А3", row_id=row_a3.id)

# Зона Б — стеллажи с уровнями
zone_b = Zone(name="Б")
db.add(zone_b)
db.flush()

row_b1 = Row(zone_id=zone_b.id, name="Б1")
row_b2 = Row(zone_id=zone_b.id, name="Б2")
db.add_all([row_b1, row_b2])
db.flush()

shelf_b1_s1 = Shelf(row_id=row_b1.id, name="С1")
shelf_b1_s2 = Shelf(row_id=row_b1.id, name="С2")
shelf_b2_s1 = Shelf(row_id=row_b2.id, name="С1")
db.add_all([shelf_b1_s1, shelf_b1_s2, shelf_b2_s1])
db.flush()

lev_b1s1u1 = Level(shelf_id=shelf_b1_s1.id, name="У1")
lev_b1s1u2 = Level(shelf_id=shelf_b1_s1.id, name="У2")
lev_b1s1u3 = Level(shelf_id=shelf_b1_s1.id, name="У3")
lev_b1s2u1 = Level(shelf_id=shelf_b1_s2.id, name="У1")
lev_b1s2u2 = Level(shelf_id=shelf_b1_s2.id, name="У2")
lev_b2s1u1 = Level(shelf_id=shelf_b2_s1.id, name="У1")
lev_b2s1u2 = Level(shelf_id=shelf_b2_s1.id, name="У2")
db.add_all([lev_b1s1u1, lev_b1s1u2, lev_b1s1u3,
            lev_b1s2u1, lev_b1s2u2, lev_b2s1u1, lev_b2s1u2])
db.flush()

addr_b1s1u1 = make_addr("Зона Б, Ряд Б1, Стеллаж С1, Уровень У1", level_id=lev_b1s1u1.id)
addr_b1s1u2 = make_addr("Зона Б, Ряд Б1, Стеллаж С1, Уровень У2", level_id=lev_b1s1u2.id)
addr_b1s1u3 = make_addr("Зона Б, Ряд Б1, Стеллаж С1, Уровень У3", level_id=lev_b1s1u3.id)
addr_b1s2u1 = make_addr("Зона Б, Ряд Б1, Стеллаж С2, Уровень У1", level_id=lev_b1s2u1.id)
addr_b1s2u2 = make_addr("Зона Б, Ряд Б1, Стеллаж С2, Уровень У2", level_id=lev_b1s2u2.id)
addr_b2s1u1 = make_addr("Зона Б, Ряд Б2, Стеллаж С1, Уровень У1", level_id=lev_b2s1u1.id)
addr_b2s1u2 = make_addr("Зона Б, Ряд Б2, Стеллаж С1, Уровень У2", level_id=lev_b2s1u2.id)

# Зона В — смешанная: один ряд без стеллажей, один со стеллажами
zone_v = Zone(name="В")
db.add(zone_v)
db.flush()

row_v1 = Row(zone_id=zone_v.id, name="В1")  # без стеллажей
row_v2 = Row(zone_id=zone_v.id, name="В2")  # со стеллажами
db.add_all([row_v1, row_v2])
db.flush()

addr_v1 = make_addr("Зона В, Ряд В1", row_id=row_v1.id)

shelf_v2_s1 = Shelf(row_id=row_v2.id, name="С1")
db.add(shelf_v2_s1)
db.flush()

lev_v2s1u1 = Level(shelf_id=shelf_v2_s1.id, name="У1")
lev_v2s1u2 = Level(shelf_id=shelf_v2_s1.id, name="У2")
db.add_all([lev_v2s1u1, lev_v2s1u2])
db.flush()

addr_v2s1u1 = make_addr("Зона В, Ряд В2, Стеллаж С1, Уровень У1", level_id=lev_v2s1u1.id)
addr_v2s1u2 = make_addr("Зона В, Ряд В2, Стеллаж С1, Уровень У2", level_id=lev_v2s1u2.id)

db.commit()
print(f"  Создано 3 зоны, адреса хранения расставлены")

# ── Товары ────────────────────────────────────────────────────────────────────
print("Создание товаров...")

products_data = [
    # (name, article, type, unit, tire_size, width, profile, diameter, season, brand, model, tire_type, load_speed, min_qty)
    ("Шина 205/55 R16 Michelin X-Ice North 4",  "MXI4-20555R16", "small", "шт", "205/55 R16", "205", "55", "R16", "winter",    "Michelin", "X-Ice North 4",  "truck",         "91T", 5),
    ("Шина 185/65 R15 Nokian Hakka Green 3",    "NHG3-18565R15", "small", "шт", "185/65 R15", "185", "65", "R15", "summer",    "Nokian",   "Hakka Green 3",  "truck",         "88H", 5),
    ("Шина 235/65 R17 Michelin Latitude Tour",  "MLT-23565R17",  "large", "шт", "235/65 R17", "235", "65", "R17", "allseason", "Michelin", "Latitude Tour",  "truck",         "104H", 3),
    ("Шина 225/50 R17 Continental PremiumContact","CPC-22550R17", "small", "шт", "225/50 R17", "225", "50", "R17", "summer",    "Continental","PremiumContact 6","truck",       "94Y", 4),
    ("Шина 215/60 R16 Bridgestone Turanza",     "BT-21560R16",   "small", "шт", "215/60 R16", "215", "60", "R16", "summer",    "Bridgestone","Turanza T005",  "truck",         "95V", 4),
    ("Шина 600/65 R38 Michelin MachXBib",       "MMX-60065R38",  "large", "шт", "600/65 R38", "600", "65", "R38", "allseason", "Michelin", "MachXBib",       "agricultural",  "153D", 2),
    ("Шина 480/65 R28 Nokian Tractor",          "NT-48065R28",   "large", "шт", "480/65 R28", "480", "65", "R28", "allseason", "Nokian",   "Tractor",        "agricultural",  "144A8", 2),
    ("Шина 12.00 R20 Кама Урал",               "KU-1200R20",    "large", "шт", "12.00 R20",  "12",  "00", "R20", "allseason", "Кама",     "Урал",           "special",       "150K", 3),
    ("Шина 315/80 R22.5 Continental HDR",       "CHD-31580R225", "large", "шт", "315/80 R22.5","315","80", "R22.5","allseason","Continental","HDR",           "special",       "156/154L", 2),
    ("Шина 175/70 R13 Pirelli Cinturato P1",    "PCP1-17570R13", "small", "шт", "175/70 R13", "175", "70", "R13", "summer",    "Pirelli",  "Cinturato P1",   "truck",         "82T", 6),
]

admin_user = db.query(User).filter(User.username == "admin").first()
prod_objs = []

for (name, article, ptype, unit, tsize, width, profile,
     diameter, season, brand, model, ttype, lsi, min_qty) in products_data:
    p = Product(
        name=name, article=article, product_type=ptype, unit=unit,
        tire_size=tsize, width=width, profile=profile, diameter=diameter,
        season=season, brand=brand, model=model, tire_type=ttype,
        load_speed_index=lsi, min_quantity=min_qty,
    )
    db.add(p)
    prod_objs.append(p)

db.commit()
print(f"  Создано {len(prod_objs)} товаров")

# ── Остатки по адресам ────────────────────────────────────────────────────────
print("Распределение остатков...")

# (product_index, address, quantity)
stock_data = [
    # Крупногабаритные — зона А (ряды)
    (5,  addr_a1, 12),   # Michelin MachXBib
    (6,  addr_a1, 8),    # Nokian Tractor
    (7,  addr_a2, 15),   # Кама Урал
    (8,  addr_a2, 6),    # Continental HDR
    (2,  addr_a3, 20),   # Michelin Latitude Tour

    # Мелкогабаритные — зона Б (стеллажи)
    (0,  addr_b1s1u1, 40),  # Michelin X-Ice North 4
    (0,  addr_b1s1u2, 25),  # Michelin X-Ice North 4 (второй адрес)
    (1,  addr_b1s1u3, 60),  # Nokian Hakka Green 3
    (3,  addr_b1s2u1, 35),  # Continental PremiumContact
    (4,  addr_b1s2u2, 45),  # Bridgestone Turanza
    (9,  addr_b2s1u1, 80),  # Pirelli Cinturato P1
    (1,  addr_b2s1u2, 30),  # Nokian Hakka Green 3 (второй адрес)

    # Зона В — смешанная
    (7,  addr_v1,     10),  # Кама Урал
    (4,  addr_v2s1u1, 20),  # Bridgestone Turanza
    (9,  addr_v2s1u2, 50),  # Pirelli Cinturato P1
]

for prod_idx, addr, qty in stock_data:
    product = prod_objs[prod_idx]
    loc = StockLocation(
        product_id=product.id,
        address_id=addr.id,
        quantity=qty,
        reserved_quantity=0,
    )
    db.add(loc)
    db.flush()
    db.add(StockOperation(
        product_id=product.id,
        operation="receipt",
        quantity=qty,
        qty_before=0,
        qty_after=qty,
        performed_by=admin_user.id,
        comment="Начальный остаток (seed)",
    ))

db.commit()
print(f"  Распределено {len(stock_data)} записей остатков")

# ── Итог ─────────────────────────────────────────────────────────────────────
print()
print("=" * 50)
print("База данных заполнена успешно!")
print()
print("Пользователи (пароль для всех: 12345678):")
print("  admin        — Администратор")
print("  manager1     — Менеджер")
print("  store1       — Кладовщик 1")
print("  store2       — Кладовщик 2")
print("  loader1      — Грузчик 1")
print("  loader2      — Грузчик 2")
print("  accountant1  — Бухгалтер")
print()
print("Склад:")
print("  Зона А — 3 ряда (крупногабаритные, без стеллажей)")
print("  Зона Б — 2 ряда со стеллажами и уровнями")
print("  Зона В — смешанная (1 ряд + 1 ряд со стеллажом)")
print("=" * 50)

db.close()
