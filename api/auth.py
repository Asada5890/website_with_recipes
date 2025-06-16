from fastapi import APIRouter, HTTPException, Depends, Request, Form
from sqlalchemy.orm import Session 
from pydantic import ValidationError
from core.settings import settings
from models.user import User
from schemas.auth import Token, UserResponse
from db.session import get_db


from schemas.user import UserCreate, UserLogin
from services.auth_service import AuthService
from services.favorite_service import FavoriteService
from services.recipe_service import RecipeService
from services.user_service import UserDoesNotExist, UserService, UniqueViolation
from core.security import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
router = APIRouter()


templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse("auth_templates/register.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    return templates.TemplateResponse("auth_templates/login.html", {"request": request})

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    auth_service: AuthService = Depends(),
    user_service: UserService = Depends()
):
    try:
        form_data = await request.form()
        user_data = UserCreate(**form_data) 
        
        user = user_service.create_user(user_data)
        token = await auth_service.register(user)
        
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="access_token", value=f"Bearer {token.access_token}", httponly=True)
        return response

    except UniqueViolation as error:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь с таким email уже существует"},
            status_code=400
        )

    

@router.post("/login", response_class=RedirectResponse)
async def login_user(
    request: Request,
    user_service: UserService = Depends(),
    auth_service: AuthService = Depends()
):
    try:
        
        form_data = await request.form()

        login_data = UserLogin(**form_data)

        user = user_service.get_user(login_data)
        if not user:
            raise UserDoesNotExist()

        token = auth_service.login(user)
        if not token or not token.access_token:
            raise ValueError("Ошибка генерации токена")

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token.access_token}",
            httponly=True,
            max_age=30*24*3600,
            path="/"
        )
        return response

    except UserDoesNotExist:
        
        return templates.TemplateResponse(
            "auth_templates/login.html",
            {
                "request": request,
                "error": "Неверный email или пароль",
            },
            status_code=401
        )
    except ValidationError as e:
        print(f"Validation error: {e.errors()}")
        return templates.TemplateResponse(
            "auth_templates/login.html",
            {"request": request, "error": "Некорректный формат данных"},
            status_code=400
        )


@router.post("/logout")
async def logout_user():
    # Создаем редирект на главную страницу
    response = RedirectResponse(url="/", status_code=303)
    
    # Удаляем куки с токеном
    response.delete_cookie(
        key="access_token",
        httponly=True,
        path="/"
    )
    
    return response


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user_service: UserService = Depends(),
    recipe_service: RecipeService = Depends(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    try:
        user_id = current_user["id"]
        user = user_service.get_user_by_id(user_id)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Получаем рецепты пользователя и избранное
        fav_service = FavoriteService(db)
        favorites = fav_service.get_user_favorites(user_id)
        favorite_recipes = []
        user_recipes = recipe_service.get_recipes_by_author(user_id)

        # Обрабатываем избранные рецепты
        for fav in favorites:
            recipe = recipe_service.get_recipe_by_id(fav.recipe_id)
            if recipe:
                recipe["_id"] = str(recipe["_id"])
                if not recipe.get("images") or not recipe["images"][0]:
                    recipe["images"] = ["/static/images/recipe-default.jpg"]
                favorite_recipes.append(recipe)
        
        # Обрабатываем рецепты пользователя
        processed_recipes = []
        for recipe in user_recipes:
            recipe["_id"] = str(recipe["_id"])
            if not recipe.get("images") or not recipe["images"][0]:
                recipe["images"] = ["/static/images/recipe-default.jpg"]
            processed_recipes.append(recipe)

        return templates.TemplateResponse(
            "global_profile.html",
            {
                "request": request,
                "user": user,
                "user_recipes": processed_recipes,
                "favorite_recipes": favorite_recipes,
                "is_owner": True,
                "current_user": current_user
            }
        )
        
    except Exception as e:
        print(f"Error loading profile: {str(e)}")
        return RedirectResponse("/", status_code=303)