from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """User table in database. We can store 3 types of user.
    customer - default user created by register endpoint
    mechanic - superuser providing services for the customers
    admin - admin account using admin endpoint as his default"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default='customer')


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    message = Column(String)


class Part(Base):
    __tablename__ = "part"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    amount_left = Column(Integer, default=1)
    engine_type = Column(String)
    price = Column(Float, default=0.00)
    nr_oem = Column(String)
    qr_code = Column(String)
    repairs = relationship("PartsInRepair", back_populates="part")


class Repair(Base):
    __tablename__ = "repair"

    id = Column(Integer, primary_key=True, index=True)
    car_name = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    active = Column(Boolean, default=False)
    customer_id = Column(Integer, ForeignKey("user.id"))
    money = Column(Float, default=0.00)
    parts = relationship("PartsInRepair", back_populates="repair")


class PartsInRepair(Base):
    __tablename__ = "parts_in_repair"

    part_id = Column(ForeignKey("part.id"), primary_key=True)
    repair_id = Column(ForeignKey("repair.id"), primary_key=True)
    quantity = Column(Integer)
    part = relationship("Part", back_populates="repairs")
    repair = relationship("Repair", back_populates="parts")
