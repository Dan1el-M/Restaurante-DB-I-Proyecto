from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    # Columnas
    restaurant_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(64), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    estado = Column(Integer, nullable=False, default=1)
    
    # Relaciones
    admin = relationship("User", back_populates="restaurants")
    menus = relationship("Menu", back_populates="restaurant", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    
    def __repr__(self):
        return f"<Restaurant(restaurant_id={self.restaurant_id}, nombre='{self.nombre}', estado={self.estado})>"