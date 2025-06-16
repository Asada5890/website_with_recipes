from datetime import datetime
from db.mongo import recipes
from bson import ObjectId

class CollectionService:
    def __init__(self):
        self.collection = recipes

class RecipeService:
    def __init__(self):
        self.collection = recipes

    def get_all_recipes(self):
        """
        Возвращает все продукты
        """
        return list(self.collection.find({}))
    

    def recepie_exists(self, recipe_id: ObjectId) -> bool:
        """
        Проверяет существование товара по ID
        """
        return bool(
            self.collection.count_documents(
                {"_id": recipe_id}, 
                limit=1
            )
        )
    
    def get_one_recepie(self, query: dict):
        """
        Возвращает один продукт по id
        """
        return self.collection.find_one(query)
   
    

    
    def get_recipes_by_author(self, user_id: int) -> list[dict]:
        """Универсальный метод с поддержкой разных типов author_id"""
        try:
        # Проверка и преобразование типа
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            
            # Создаем правильный фильтр в виде словаря
            query = {"user_id": user_id}
            
            # Выполняем запрос с фильтром
            recipes_cursor = self.collection.find(query)
            
            # Преобразуем курсор в список словарей
            recipes_list = []
            for recipe in recipes_cursor:
                # Конвертируем ObjectId в строку
                recipe["_id"] = str(recipe["_id"])
                recipes_list.append(recipe)
            
            return recipes_list
        except Exception as e:
            print(f"Error in get_recipes_by_author: {e}")
            return []
        


    def add_recipe(self, recipe_data: dict):
        """
        Добавляет новый рецепт в базу данных
        """
        # Убедимся, что все необходимые поля есть
        if not recipe_data.get("created_at"):
            recipe_data["created_at"] = datetime.utcnow()
        
        if "images" not in recipe_data:
            recipe_data["images"] = []
            
        if "featured" not in recipe_data:
            recipe_data["featured"] = False
            
        # Вставляем рецепт в коллекцию
        result = self.collection.insert_one(recipe_data)
        return str(result.inserted_id)
    
    def get_recipe_by_id(self, recipe_id):
        if isinstance(recipe_id, str):
            recipe_id = ObjectId(recipe_id)
        return self.collection.find_one({"_id": recipe_id})
    
    def get_all_categories(self):
        """
        Возвращает все категории
        """
        return self.collection.distinct("category")
    

    def update_recipe(self, recipe_id: str, update_data: dict) -> bool:
        """
        Обновляет рецепт по ID
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(recipe_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating recipe: {str(e)}")
            return False
    
    def get_recepies_by_category(self, category_name):
        """
        Возвращает все продукты по категории
        """
        return list(self.collection.find({"category": category_name}))

    def sort_products(self):
        """
        сортировка 
        """
    
    def update_product(self, recipe_id: str, name: str, category: str, price: float, description: str):
        """
        Обновление данных товара в базе данных.
        """
        recepie_id = ObjectId(recipe_id)
        
        updated_product = self.collection.update_one(
            {"_id": recepie_id},
            {"$set": {"name": name, "category": category, "price": price, "description": description}}
        )

        if updated_product.modified_count == 0:
            raise Exception(f"Ошибка при обновлении товара. Возможно, данные не изменились.")

        return self.collection.find_one({"_id": recipe_id})
    
    def delete_recepie_by_id(self, recipe_id: str):
        """
        Удаление продукта по ID
        """
        result = self.collection.delete_one({"_id": ObjectId(recipe_id)})
        return result.deleted_count > 0  # Возвращаем True, если удален хотя бы один продукт
