from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    rows = relationship("Row", back_populates="zone", cascade="all, delete-orphan")


class Row(Base):
    __tablename__ = "rows"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(50), nullable=False)

    zone = relationship("Zone", back_populates="rows")
    shelves = relationship("Shelf", back_populates="row", cascade="all, delete-orphan")


class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True)
    row_id = Column(Integer, ForeignKey("rows.id"), nullable=False)
    name = Column(String(50), nullable=False)

    row = relationship("Row", back_populates="shelves")
    levels = relationship("Level", back_populates="shelf", cascade="all, delete-orphan")


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id"), nullable=False)
    name = Column(String(50), nullable=False)

    shelf = relationship("Shelf", back_populates="levels")


class StorageAddress(Base):
    __tablename__ = "storage_addresses"

    id = Column(Integer, primary_key=True)
    address_type = Column(String(20), nullable=False)  # zone_row or zone_row_shelf_level
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    row_id = Column(Integer, ForeignKey("rows.id"), nullable=False)
    shelf_id = Column(Integer, ForeignKey("shelves.id"), nullable=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)
    display_name = Column(String(100), nullable=False)

    zone = relationship("Zone")
    row = relationship("Row")
    shelf = relationship("Shelf")
    level = relationship("Level")
    products = relationship("Product", back_populates="address")
