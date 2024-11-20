class Food:
    def __init__(self, name, calories, protein, fat, carbs):
        self.name = name
        self.calories = calories  # kcal
        self.protein = protein    # g
        self.fat = fat           # g
        self.carbs = carbs       # g

class NutritionCalculator:
    def __init__(self):
        self.foods = []
    
    def add_food(self, name, calories, protein, fat, carbs):
        food = Food(name, calories, protein, fat, carbs)
        self.foods.append(food)
    
    def calculate_total(self):
        total_calories = sum(food.calories for food in self.foods)
        total_protein = sum(food.protein for food in self.foods)
        total_fat = sum(food.fat for food in self.foods)
        total_carbs = sum(food.carbs for food in self.foods)
        
        return {
            'calories': total_calories,
            'protein': total_protein,
            'fat': total_fat,
            'carbs': total_carbs
        }
    
    def calculate_pfc_ratio(self):
        totals = self.calculate_total()
        
        # PFCバランスの計算（カロリーベース）
        protein_cal = totals['protein'] * 4  # タンパク質は1gあたり4kcal
        fat_cal = totals['fat'] * 9         # 脂質は1gあたり9kcal
        carbs_cal = totals['carbs'] * 4     # 炭水化物は1gあたり4kcal
        total_cal = protein_cal + fat_cal + carbs_cal
        
        if total_cal == 0:
            return {'protein': 0, 'fat': 0, 'carbs': 0}
        
        return {
            'protein': round(protein_cal / total_cal * 100, 1),
            'fat': round(fat_cal / total_cal * 100, 1),
            'carbs': round(carbs_cal / total_cal * 100, 1)
        }
    
    def print_summary(self):
        totals = self.calculate_total()
        pfc_ratio = self.calculate_pfc_ratio()
        
        print("\n=== 栄養摂取サマリー ===")
        print(f"総カロリー: {totals['calories']}kcal")
        print(f"\n各栄養素:")
        print(f"タンパク質: {totals['protein']}g")
        print(f"脂質: {totals['fat']}g")
        print(f"炭水化物: {totals['carbs']}g")
        print(f"\nPFCバランス:")
        print(f"タンパク質: {pfc_ratio['protein']}%")
        print(f"脂質: {pfc_ratio['fat']}%")
        print(f"炭水化物: {pfc_ratio['carbs']}%")

# 使用例
calculator = NutritionCalculator()