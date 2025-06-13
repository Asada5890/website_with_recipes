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
   
    
    def get_recipe_by_id(self, recipe_id):
        if isinstance(recipe_id, str):
            recipe_id = ObjectId(recipe_id)
        return self.collection.find_one({"_id": recipe_id})
    
    def get_all_categories(self):
        """
        Возвращает все категории
        """
        return self.collection.distinct("category")
    
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
