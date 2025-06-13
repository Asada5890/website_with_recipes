from pymongo import MongoClient
from core.settings import settings

server = MongoClient(settings.MONGODB_URL, settings.MONGODB_PORT)

recipes_db = server[settings.MONGODB_DB_NAME]

recipes = recipes_db[settings.MONGODB_COLLECTION_RECIPES]




data = recipes.find({})
