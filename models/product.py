from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    article = Column(String(100), unique=True, nullable=False, index=True)
    product_type = Column(String(20), nullable=False)  # large, small
    unit = Column(String(10), nullable=False)  # шт, кг

    # Параметры шины
    tire_size = Column(String(50), nullable=True)        # 205/55 R16
    width = Column(String(20), nullable=True)            # 205
    profile = Column(String(20), nullable=True)          # 55
    diameter = Column(String(20), nullable=True)         # R16
    season = Column(String(20), nullable=True)           # summer/winter/allseason
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    tire_type = Column(String(50), nullable=True)        # agricultural/truck/special
    load_speed_index = Column(String(20), nullable=True) # 91H

    min_quantity = Column(Numeric(10, 2), default=0)
    photo_path = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="product")
    stock_operations = relationship("StockOperation", back_populates="product")
    stock_locations = relationship("StockLocation", back_populates="product", cascade="all, delete-orphan")

    @property
    def quantity(self):
        return sum(float(sl.quantity or 0) for sl in self.stock_locations)

    @property
    def reserved_quantity(self):
        return sum(float(sl.reserved_quantity or 0) for sl in self.stock_locations)

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        if self.min_quantity and float(self.min_quantity) > 0:
            return self.quantity <= float(self.min_quantity)
        return False

    SEASON_LABELS = {"summer": "Лето", "winter": "Зима", "allseason": "Всесезонная"}
    TIRE_TYPE_LABELS = {
        "agricultural": "Сельхозтехника",
        "truck": "Грузовая техника",
        "special": "Спецтехника",
    }

    @property
    def season_label(self):
        return self.SEASON_LABELS.get(self.season, self.season or "—")

    @property
    def tire_type_label(self):
        return self.TIRE_TYPE_LABELS.get(self.tire_type, self.tire_type or "—")


class StockLocation(Base):
    __tablename__ = "stock_locations"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("storage_addresses.id"), nullable=False)
    quantity = Column(Numeric(10, 2), default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)

    product = relationship("Product", back_populates="stock_locations")
    address = relationship("StorageAddress", back_populates="stock_locations")
