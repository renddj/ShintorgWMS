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
    quantity = Column(Numeric(10, 2), default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)
    min_quantity = Column(Numeric(10, 2), default=0)
    address_id = Column(Integer, ForeignKey("storage_addresses.id"), nullable=True)
    photo_path = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    address = relationship("StorageAddress", back_populates="products")
    tasks = relationship("Task", back_populates="product")
    stock_operations = relationship("StockOperation", back_populates="product")

    @property
    def available_quantity(self):
        return float(self.quantity or 0) - float(self.reserved_quantity or 0)

    @property
    def is_low_stock(self):
        if self.min_quantity and self.min_quantity > 0:
            return float(self.quantity or 0) <= float(self.min_quantity)
        return False
