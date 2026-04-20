from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class Role(Base):
    __tablename__ = "roles"
    
    # Columnas
    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name = Column(String(64), nullable=False)
    
    # Relaciones
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"