from sqlalchemy import Column, Integer, String, ForeignKey
from db.session import Base
from sqlalchemy.orm import relationship

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(String)  

    user = relationship("User", back_populates="favorites")