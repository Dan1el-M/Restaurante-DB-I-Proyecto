# models/order_items.py
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class OrderItem(Base):
    __tablename__ = "order_items"
    
    order_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.menu_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones
    order = relationship("Order", back_populates="items")
    menu = relationship("Menu", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(order_item_id={self.order_item_id}, quantity={self.quantity}, price={self.price})>"