from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base

class Menu(Base):
    __tablename__ = "menus"
    
    # Columnas
    menu_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dish_name = Column(String(64), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    # Relaciones
    restaurant = relationship("Restaurant", back_populates="menus")
    order_items = relationship("OrderItem", back_populates="menu")
    
    # Restricciones
    # No pueden existir dos platos con el mismo nombre
    __table_args__ = (
        UniqueConstraint('restaurant_id', 'dish_name', name='unique_dish_per_restaurant'),
    )
    
    def __repr__(self):
        return f"<Menu(menu_id={self.menu_id}, dish_name='{self.dish_name}', price={self.price})>"