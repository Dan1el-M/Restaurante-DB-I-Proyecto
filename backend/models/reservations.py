# models/reservations.py
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from ..database import Base

class Reservation(Base):
    __tablename__ = "reservations"
    
    reservation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.table_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reservation_date = Column(TIMESTAMP, nullable=False)
    reservation_status = Column(Integer, nullable=False)
    
    # Relaciones
    table = relationship("Table", back_populates="reservations")
    client = relationship("User", back_populates="reservations")
    
    def __repr__(self):
        return f"<Reservation(reservation_id={self.reservation_id}, reservation_status={self.reservation_status})>"