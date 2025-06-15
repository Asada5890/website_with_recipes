from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    user_id: int
    recipe_id: str

class FavoriteResponse(FavoriteCreate):
    id: int

    class Config:
        orm_mode = True