from datetime import datetime
from pathlib import Path
import uuid
from bson import ObjectId
from fastapi import File, Request, HTTPException, APIRouter,Depends, UploadFile
from bson.errors import InvalidId
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from core.security import get_current_user
from services.favorite_service import FavoriteService
from db.session import get_db
from sqlalchemy.orm import Session 


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
    db: Session = Depends(get_db),  # Добавлено
    current_user: dict = Depends(get_current_user)
):
    # Получаем все рецепты
    recipes = recipe_service.get_all_recipes()
    fav_service = FavoriteService(db)
    # Для каждого рецепта:
    for recipe in recipes:
        # 1. Преобразуем ObjectId в строку
        recipe["_id"] = str(recipe["_id"])
        

        if current_user:
            recipe["is_favorite"] = fav_service.is_recipe_in_favorites(
                current_user["id"], 
                str(recipe["_id"])
            )
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

        recipe = recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        

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
    db: Session = Depends(get_db),
    recipe_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    fav_service = FavoriteService(db)
    favorites = fav_service.get_user_favorites(user_id)
    favorite_recipes = []
    user_recipes = recipe_service.get_recipes_by_author(user_id)

    for fav in favorites:
        recipe = recipe_service.get_recipe_by_id(fav.recipe_id)
        if recipe:
            recipe["_id"] = str(recipe["_id"])

            if not recipe.get("images") or not recipe["images"][0]:
                recipe["images"] = ["images/recipe-default.jpg"]
            favorite_recipes.append(recipe)
    

    processed_recipes = []
    for recipe in user_recipes:
        recipe["_id"] = str(recipe["_id"])
        # Добавляем URL изображения по умолчанию, если нет изображения
        if not recipe.get("images") or not recipe["images"][0]:
            recipe["images"] = ["/static/images/recipe-default.jpg"]
        processed_recipes.append(recipe)

    is_owner = current_user and current_user.get("id") == user_id

    return templates.TemplateResponse("global_profile.html", {
        "favorite_recipes": favorite_recipes,
        "request": request,
        "user": user,  
        "user_recipes": processed_recipes,
        "is_owner": is_owner,
        "current_user": current_user
    })



from fastapi import Form

# Определяем базовый каталог проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Путь к папке static/images
IMAGES_DIR = BASE_DIR / "static" / "images"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
@router.get('/add', response_class=HTMLResponse)
async def add_recipe_form(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    return templates.TemplateResponse("add_recipe.html", {
        "request": request,
        "user": current_user
    })

@router.post('/add', response_class=HTMLResponse)
async def add_recipe(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    cooking_time: int = Form(...),
    difficulty: str = Form(...),
    servings: int = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(None),  
    current_user: dict = Depends(get_current_user),
    recipe_service: RecipeService = Depends()
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    try:
        # Обработка изображения
        image_path = None
        if image and image.filename:
            # Генерируем уникальное имя файла
            file_extension = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = IMAGES_DIR / filename
            
            # Сохраняем файл
            with open(file_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            # Путь для сохранения в БД
            image_path = f"/static/images/{filename}"

        # Собираем данные рецепта
        recipe_data = {
            "user_id": current_user["id"],
            "name": name,
            "description": description,
            "cooking_time": cooking_time,
            "difficulty": difficulty,
            "servings": servings,
            "ingredients": [ing.strip() for ing in ingredients.split('\n') if ing.strip()],
            "instructions": [inst.strip() for inst in instructions.split('\n') if inst.strip()],
            "category": category,
            "created_at": datetime.utcnow(),
            "images": [image_path] if image_path else [],
            "featured": False
        }
        
        # Добавляем рецепт в базу
        recipe_id = recipe_service.add_recipe(recipe_data)
        return RedirectResponse(f"/recipe/{recipe_id}", status_code=303)
    
    except Exception as e:
        print(f"Error adding recipe: {str(e)}")
        return templates.TemplateResponse("add_recipe.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка при добавлении рецепта: {str(e)}"
        }, status_code=400)
    

@router.get('/recipe/{recipe_id}/edit', response_class=HTMLResponse)
async def edit_recipe_form(
    request: Request,
    recipe_id: str,
    recipe_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    # Проверяем, что текущий пользователь - автор рецепта
    if recipe.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    return templates.TemplateResponse(
        "edit_recipe.html",
        {
            "request": request,
            "recipe": recipe,
            "user": current_user
        }
    )

@router.post('/recipe/{recipe_id}/edit', response_class=HTMLResponse)
async def update_recipe(
    request: Request,
    recipe_id: str,
    name: str = Form(...),
    description: str = Form(...),
    cooking_time: int = Form(...),
    difficulty: str = Form(...),
    servings: int = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(None),
    current_user: dict = Depends(get_current_user),
    recipe_service: RecipeService = Depends()
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    # Проверяем существование рецепта и права доступа
    existing_recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    if existing_recipe.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    try:
        # Обработка изображения
        image_path = None
        if image and image.filename:
            file_extension = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = IMAGES_DIR / filename
            
            with open(file_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            image_path = f"/static/images/{filename}"
        
        # Подготавливаем данные для обновления
        update_data = {
            "name": name,
            "description": description,
            "cooking_time": cooking_time,
            "difficulty": difficulty,
            "servings": servings,
            "ingredients": [ing.strip() for ing in ingredients.split('\n') if ing.strip()],
            "instructions": [inst.strip() for inst in instructions.split('\n') if inst.strip()],
            "category": category,
            "updated_at": datetime.utcnow()
        }
        
        if image_path:
            update_data["images"] = [image_path]
        
        # Обновляем рецепт
        result = recipe_service.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise Exception("Рецепт не был обновлен")
        
        return RedirectResponse(f"/recipe/{recipe_id}", status_code=303)
    
    except Exception as e:
        print(f"Error updating recipe: {str(e)}")
        return templates.TemplateResponse(
            "edit_recipe.html",
            {
                "request": request,
                "recipe": existing_recipe,
                "user": current_user,
                "error": f"Ошибка при обновлении рецепта: {str(e)}"
            },
            status_code=400
        )

@router.post('/recipe/{recipe_id}/delete', response_class=RedirectResponse)
async def delete_recipe(
    request: Request,
    recipe_id: str,
    current_user: dict = Depends(get_current_user),
    recipe_service: RecipeService = Depends()
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    recipe = recipe_service.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    if recipe.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    try:
        deleted = recipe_service.delete_recepie_by_id(recipe_id)
        if not deleted:
            raise Exception("Рецепт не был удален")
        
        return RedirectResponse("/profile", status_code=303)
    
    except Exception as e:
        print(f"Error deleting recipe: {str(e)}")
        return RedirectResponse(
            f"/recipe/{recipe_id}",
            status_code=303
        )