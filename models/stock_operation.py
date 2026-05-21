from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class StockOperation(Base):
    __tablename__ = "stock_operations"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    operation = Column(String(20), nullable=False)  # receipt, shipment, writeoff
    quantity = Column(Numeric(10, 2), nullable=False)
    qty_before = Column(Numeric(10, 2), nullable=False)
    qty_after = Column(Numeric(10, 2), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    product = relationship("Product", back_populates="stock_operations")
    performer = relationship("User", back_populates="stock_operations")
    task = relationship("Task")

    OP_LABELS = {
        "receipt": "Приёмка",
        "shipment": "Отгрузка",
        "writeoff": "Списание",
        "move_out": "Перемещение (откуда)",
        "move_in": "Перемещение (куда)",
    }

    @property
    def operation_label(self):
        return self.OP_LABELS.get(self.operation, self.operation)
