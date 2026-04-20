from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base

class Table(Base):
    __tablename__ = "tables"
    
    # Columnas
    table_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_number = Column(Integer, nullable=False)
    estado = Column(Integer, nullable=False, default=1)  # 1 = disponible, 0 = ocupada, 2 = reservada
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    # Relaciones
    restaurant = relationship("Restaurant", back_populates="tables")
    orders = relationship("Order", back_populates="table")
    reservations = relationship("Reservation", back_populates="table")
    
    # Restricciones
    __table_args__ = (
        UniqueConstraint('restaurant_id', 'table_number', name='unique_table_per_restaurant'),
    )
    
    def __repr__(self):
        return f"<Table(table_id={self.table_id}, table_number={self.table_number}, estado={self.estado})>"