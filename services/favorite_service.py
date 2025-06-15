from bson import ObjectId
from fastapi import logger
from sqlalchemy.orm import Session
from models.favorites import Favorite
from schemas.favorites import FavoriteCreate
from models.user import User  # Импортируйте модель User

class FavoriteService:
    def __init__(self, db: Session):
        self.db = db

    def add_to_favorites(self, favorite: FavoriteCreate) -> Favorite:
        # Проверяем, не добавлен ли уже рецепт
        existing = self.db.query(Favorite).filter(
            Favorite.user_id == favorite.user_id,
            Favorite.recipe_id == favorite.recipe_id
        ).first()
        
        if existing:
            return existing
        
        new_favorite = Favorite(**favorite.dict())
        self.db.add(new_favorite)
        self.db.commit()
        self.db.refresh(new_favorite)
        return new_favorite

    
    def remove_from_favorites(self, user_id: int, recipe_id: str) -> bool:
        try:
            # Проверяем существование записи
            favorite = self.db.query(Favorite).filter(
                Favorite.user_id == user_id,
                Favorite.recipe_id == recipe_id
            ).first()
            
            if not favorite:
                return False
                
            # Удаляем запись
            self.db.delete(favorite)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error removing favorite: {str(e)}")
            return False

    def get_user_favorites(self, user_id: int) -> list[Favorite]:
        return self.db.query(Favorite).filter(
            Favorite.user_id == user_id
        ).all()

    def is_recipe_in_favorites(self, user_id: int, recipe_id: str) -> bool:
        return self.db.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.recipe_id == recipe_id
        ).count() > 0