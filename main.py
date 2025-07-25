import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from api import auth, recipe, favorites, no_main_pages
from db.session import init



app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Монтируем папку для изображений
app.mount(
    "/images", 
    StaticFiles(directory=os.path.join(BASE_DIR, "static", "images")), 
    name="images"
)

# Монтируем общую папку static для остальных файлов
app.mount(
    "/static", 
    StaticFiles(directory=os.path.join(BASE_DIR, "static")), 
    name="static"
)

# app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Сначала добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Затем подключаем роутеры

app.include_router(auth.router, prefix='', tags=["auth"]) # Ауентификация
app.include_router(recipe.router, prefix='', tags=["recipe"]) # Рецепты
app.include_router(favorites.router, prefix='', tags=["favorites"]) # Избранное
app.include_router(no_main_pages.router, prefix='', tags=["no_main_pages"]) # второстепенные страницы



# Инициализация БД
init()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)