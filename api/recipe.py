from fastapi import FastAPI, Request, HTTPException, APIRouter,Depends
from bson.errors import InvalidId
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from core.security import get_current_user


from services.recipe_service import RecipeService
from services.user_service import UserService
import templates
from core.security import get_current_user


router = APIRouter()

templates = Jinja2Templates(directory="templates")
@router.get('/', response_class=HTMLResponse)
def main_page(
    request: Request,
    recipe_service: RecipeService = Depends(),
    user_service: UserService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    # Получаем все рецепты
    recipes = recipe_service.get_all_recipes()
    
    # Для каждого рецепта:
    for recipe in recipes:
        # 1. Преобразуем ObjectId в строку
        recipe["_id"] = str(recipe["_id"])
        
        # 2. Получаем информацию об авторе
        author_id = recipe.get("user_id")
        if author_id:
            try:
                # Получаем данные пользователя
                author = user_service.get_user_by_id(author_id)
                
                # Добавляем только нужные поля в рецепт
                recipe["author"] = {
                    "id": author.id,
                    "user_name": author.user_name,
                }
            except Exception as e:
                # На случай если пользователь не найден
                recipe["author"] = {
                    "username": "Неизвестный автор",
                }
        else:
            # Если автор не указан
            recipe["author"] = {
                "username": "Автор не указан",
                "profile_pic": "default.jpg"
            }
    
    return templates.TemplateResponse("index.html", 
                                      {"request": request,
                                       "recipes": recipes,
                                       "user": current_user}
                                    )



@router.get('/recipe/{recipe_id}', response_class=HTMLResponse)
def recipe_detail(
    request: Request,
    recipe_id: str,
    recipe_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Получаем рецепт по ID
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Преобразуем ObjectId в строку
        recipe["_id"] = str(recipe["_id"])
        
        return templates.TemplateResponse(
            "recipe_detail.html",
            {
                "request": request,
                "recipe": recipe,
                "user": current_user
            }
        )
        
    except InvalidId:
        raise HTTPException(status_code=400, detail="Неверный ID рецепта")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
    
@router.get("/profile/{user_id}", response_class=HTMLResponse)
async def view_user_profile(
    request: Request,
    user_id: int,
    user_service: UserService = Depends(),
    recipe_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    # Получаем данные пользователя
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Получаем рецепты пользователя
    user_recipes = recipe_service.get_recipes_by_author(user_id)
    print(f"Found {len(user_recipes)} recipes for user {user_id}")  # Для отладки

    # Преобразуем ObjectId и добавляем дополнительные поля
    processed_recipes = []
    for recipe in user_recipes:
        recipe["_id"] = str(recipe["_id"])
        # Добавляем URL изображения по умолчанию, если нет изображения
        if not recipe.get("images") or not recipe["images"][0]:
            recipe["images"] = ["/static/images/recipe-default.jpg"]
        processed_recipes.append(recipe)

    # Проверяем владельца профиля
    is_owner = current_user and current_user.get("id") == user_id
    print(f"User ID: {user_id}")
    print(f"User data: {user}")
    print(f"Recipes found: {user_recipes}")
    return templates.TemplateResponse("global_profile.html", {
        "request": request,
        "user": user,  # Передаём весь объект user
        "user_recipes": processed_recipes,
        "is_owner": is_owner,
        "current_user": current_user
    })