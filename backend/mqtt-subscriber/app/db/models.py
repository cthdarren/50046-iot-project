from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Mall(Base):
    __tablename__ = "malls"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # one mall to many toilets
    toilets = relationship("Toilet", back_populates="mall")
    
class Toilet(Base):
    __tablename__ = "toilets"
    id = Column(Integer, primary_key=True)
    level = Column(String, nullable=False)
    description = Column(String)
    gender = Column(String, nullable=False)
    mall_id = Column(Integer, ForeignKey("malls.id"))
    mall = relationship("Mall", back_populates="toilets")
    cubicles = relationship("Cubicle", back_populates="toilet")

class Cubicle(Base):
    __tablename__ = "cubicles"
    id = Column(Integer, primary_key=True)
    toilet_id = Column(Integer, ForeignKey("toilets.id"))
    toilet = relationship("Toilet", back_populates="cubicles")
    # only one row in state table for each cubicle
    cubicle_state = relationship("CubicleState", back_populates="cubicle", uselist=False)
    cubicle_events = relationship("CubicleEvent", back_populates="cubicle")
    
class CubicleState(Base):
    __tablename__ = "cubicle_states"
    id = Column(Integer, primary_key=True)
    cubicle_id = Column(Integer, ForeignKey("cubicles.id"), nullable=False)
    occupied = Column(Boolean, nullable=False)
    toilet_roll_percentage = Column(Float)
    updated_at = Column(DateTime, default=datetime.now)
    cubicle = relationship("Cubicle", back_populates="cubicle_state")

class CubicleEvent(Base):
    __tablename__ = "cubicle_events"
    id = Column(Integer, primary_key=True)
    cubicle_id = Column(Integer, ForeignKey("cubicles.id"), nullable=False)
    occupied = Column(Boolean)
    toilet_roll_percentage = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    cubicle = relationship("Cubicle", back_populates="cubicle_events")