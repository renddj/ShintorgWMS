from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_type = Column(String(20), nullable=False, default="shipment")  
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="new")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)
    problem_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    to_address_id = Column(Integer, ForeignKey("storage_addresses.id"), nullable=True) 
    closed_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="tasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks_created")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks_assigned")
    lines = relationship("TaskLine", back_populates="task", cascade="all, delete-orphan")
    to_address = relationship("StorageAddress", foreign_keys=[to_address_id])

    STATUS_LABELS = {
        "new": "Новое",
        "planning": "Планирование",
        "in_progress": "В работе",
        "problem": "Проблема",
        "done": "Выполнено",
        "cancelled": "Отменено",
    }
    STATUS_CLASSES = {
        "new": "badge-new",
        "planning": "badge-planning",
        "in_progress": "badge-progress",
        "problem": "badge-problem",
        "done": "badge-done",
        "cancelled": "badge-cancelled",
    }
    TYPE_LABELS = {"shipment": "Отгрузка", "receipt": "Приёмка", "move": "Перемещение"}

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def status_class(self):
        return self.STATUS_CLASSES.get(self.status, "")

    @property
    def type_label(self):
        return self.TYPE_LABELS.get(self.task_type, self.task_type)

    @property
    def planned_quantity(self):
        return sum(float(l.quantity or 0) for l in self.lines)


class TaskLine(Base):
    __tablename__ = "task_lines"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("storage_addresses.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)

    task = relationship("Task", back_populates="lines")
    address = relationship("StorageAddress")
