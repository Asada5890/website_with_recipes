from fastapi import APIRouter, HTTPException, Depends, Request, Form
from jose import JWTError
import jwt
from pydantic import ValidationError
from core.settings import settings
from models.user import User
from schemas.auth import Token, UserResponse

from schemas.user import UserCreate, UserLogin
from services.auth_service import AuthService
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
            "login.html",
            {
                "request": request,
                "error": "Неверный email или пароль",
            },
            status_code=401
        )
    except ValidationError as e:
        print(f"Validation error: {e.errors()}")
        return templates.TemplateResponse(
            "login.html",
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
def profile_page(request: Request):
    # Проверяем наличие токена в куках
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="auth_templates/login", status_code=303)
    
    try:
        # Декодируем токен
        payload = jwt.decode(
            token.replace("Bearer ", ""),
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Извлекаем данные пользователя из payload
        user_email = payload.get("email")  
        user_role = payload.get("role")


        
    except (JWTError, KeyError):
        # Обработка невалидного токена
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie("access_token")
        return response
    
    # Передаем данные в шаблон профиля
    return templates.TemplateResponse(
        "auth_templates/profile.html",
        {
            "request": request,
            "user_email": user_email,
            "user_role": user_role
        }
    )