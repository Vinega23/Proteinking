from django.contrib import admin
from .models import FoodItem, UserProfile, DailyIntake, FoodEntry, FavoriteFood

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'protein_per_100g', 'calories_per_100g', 'brand_owner']
    search_fields = ['name', 'brand_owner']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_protein_goal', 'weight', 'activity_level']

@admin.register(DailyIntake)
class DailyIntakeAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_protein', 'total_calories']
    list_filter = ['date']

@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_item', 'amount_grams', 'protein_consumed', 'meal_type', 'created_at']
    list_filter = ['meal_type', 'created_at']

@admin.register(FavoriteFood)
class FavoriteFoodAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_item', 'default_amount']

