from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from db.session import get_db
from services import user_service
from services.favorite_service import FavoriteService
from schemas.favorites import FavoriteCreate, FavoriteResponse
from core.security import get_current_user
import logging

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

from services.recipe_service import RecipeService

router = APIRouter()

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from services.favorite_service import FavoriteService
from schemas.favorites import FavoriteCreate
from db.session import get_db
from core.security import get_current_user

router = APIRouter()

@router.post("/favorites/toggle")
def toggle_favorite(
    request: Request,
    recipe_id: str = Form(...),
    user_id: int = Form(...),
    is_favorite: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Проверка прав доступа
    if not current_user or current_user["id"] != user_id:
        return RedirectResponse("/login", status_code=303)
    
    service = FavoriteService(db)
    is_favorite_bool = is_favorite.lower() == 'true'
    
    if is_favorite_bool:
        # Удаляем из избранного
        service.remove_from_favorites(user_id, recipe_id)
        message = "Рецепт удален из избранного"
    else:
        # Добавляем в избранное
        favorite = FavoriteCreate(user_id=user_id, recipe_id=recipe_id)
        service.add_to_favorites(favorite)
        message = "Рецепт добавлен в избранное"
    
    # Возвращаемся на предыдущую страницу с сообщением
    referer = request.headers.get("Referer", "/")
    return RedirectResponse(f"{referer}?message={message}", status_code=303)


@router.post("/favorites/remove")
async def remove_favorite(
    request: Request,
    recipe_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    try:
        # Создаем сервис для работы с избранным
        service = FavoriteService(db)
        
        # Пытаемся удалить запись
        success = service.remove_from_favorites(
            user_id=current_user["id"],
            recipe_id=recipe_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Рецепт не найден в избранном"
            )
            
        # Возвращаем пользователя на страницу избранного
        return RedirectResponse(
            "/favorites?message=Рецепт+удалён+из+избранного",
            status_code=303
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении из избранного: {str(e)}"
        )

    
@router.get("/", response_model=list[FavoriteResponse])
def get_user_favorites(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = FavoriteService(db)
    return service.get_user_favorites(current_user["id"])




@router.get("/favorites", response_class=HTMLResponse)
async def favorites_page(
    request: Request,
    db: Session = Depends(get_db),
    recipe_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):

    fav_service = FavoriteService(db)
    favorites = fav_service.get_user_favorites(current_user["id"])
    favorite_recipes = []
    
    for fav in favorites:
        recipe = recipe_service.get_recipe_by_id(fav.recipe_id)
        if recipe:
            recipe["_id"] = str(recipe["_id"])
            # Получаем информацию об авторе
            author_id = recipe.get("user_id")
            if author_id:
                try:
                    author = user_service.get_user_by_id(author_id)
                    recipe["author"] = {
                        "id": author.id,
                        "user_name": author.user_name
                    }
                except:
                    recipe["author"] = {"user_name": "Неизвестный автор"}
            else:
                recipe["author"] = {"user_name": "Автор не указан"}
            
            # Обработка изображения
            if not recipe.get("images") or not recipe["images"][0]:
                recipe["images"] = ["/static/images/recipe-default.jpg"]
            favorite_recipes.append(recipe)
    
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "favorite_recipes": favorite_recipes,
        "user": current_user
    })