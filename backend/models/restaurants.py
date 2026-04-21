from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    # Columnas
    restaurant_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    restaurant_name = Column(String(64), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    restaurant_status = Column(Integer, nullable=False, default=1)
    
    # Relaciones
    admin = relationship("User", back_populates="restaurants")
    menus = relationship("Menu", back_populates="restaurant", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    
    def __repr__(self):
        return f"<Restaurant(restaurant_id={self.restaurant_id}, restaurant_name='{self.restaurant_name}', restaurant_status={self.restaurant_status})>"