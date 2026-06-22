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
    address = relationship("StorageAddress", back_populates="row",
                           uselist=False, cascade="all, delete-orphan")


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
    address = relationship("StorageAddress", back_populates="level",
                           uselist=False, cascade="all, delete-orphan")


class StorageAddress(Base):
    __tablename__ = "storage_addresses"

    id = Column(Integer, primary_key=True)
    row_id = Column(Integer, ForeignKey("rows.id"), nullable=True, unique=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=True, unique=True)
    display_name = Column(String(200), nullable=False)

    row = relationship("Row", back_populates="address")
    level = relationship("Level", back_populates="address")
    stock_locations = relationship("StockLocation", back_populates="address")

    @property
    def zone(self):
        if self.row:
            return self.row.zone
        if self.level and self.level.shelf and self.level.shelf.row:
            return self.level.shelf.row.zone
        return None
