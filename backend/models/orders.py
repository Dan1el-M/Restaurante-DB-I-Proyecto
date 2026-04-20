# models/orders.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Order(Base):
    __tablename__ = "orders"
    
    orders_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.table_id"), nullable=True)
    client_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    orders_type = Column(String(64), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.restaurant_id"), nullable=False)
    
    # Relaciones
    table = relationship("Table", back_populates="orders")
    client = relationship("User", back_populates="orders_as_client")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    
    def __repr__(self):
        return f"<Order(orders_id={self.orders_id}, orders_type='{self.orders_type}')>"