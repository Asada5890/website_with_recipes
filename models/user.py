from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  
    phone_number = Column(String(20), nullable=True)

    
    favorites = relationship("Favorite", back_populates="user")