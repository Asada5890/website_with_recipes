from fastapi import FastAPI, Request, HTTPException, APIRouter,Depends
from bson.errors import InvalidId
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from core.security import get_current_user


from services.recipe_service import RecipeService
import templates
from core.security import get_current_user


router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get('/', response_class=HTMLResponse)
def main_page(
    request: Request,
    recepie_service: RecipeService = Depends(),
    current_user: dict = Depends(get_current_user)
):
    recipes = recepie_service.get_all_recipes()
    
    
    for recipe in recipes:
        recipe["_id"] = str(recipe["_id"])

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