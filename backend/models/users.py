from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    # Columnas
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(64), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    restaurants = relationship("Restaurant", back_populates="admin")
    orders = relationship("Order", back_populates="client")
    reservations = relationship("Reservation", back_populates="client")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}', role_id={self.role_id})>"