from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="new")
    # new, in_progress, problem, done, cancelled
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)
    problem_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="tasks")
    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks_created")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks_assigned")

    STATUS_LABELS = {
        "new": "Новое",
        "in_progress": "В работе",
        "problem": "Проблема",
        "done": "Выполнено",
        "cancelled": "Отменено",
    }

    STATUS_CLASSES = {
        "new": "status-new",
        "in_progress": "status-in-progress",
        "problem": "status-problem",
        "done": "status-done",
        "cancelled": "status-cancelled",
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def status_class(self):
        return self.STATUS_CLASSES.get(self.status, "")
