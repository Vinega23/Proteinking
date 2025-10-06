from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FoodItem, UserProfile, DailyIntake, FoodEntry, FavoriteFood

class FoodItemSerializer(serializers.ModelSerializer):
    """Serializer for food items with nutritional information"""
    
    class Meta:
        model = FoodItem
        fields = [
            'id', 'fdc_id', 'name', 'brand_owner',
            'protein_per_100g', 'calories_per_100g', 'carbs_per_100g',
            'fat_per_100g', 'fiber_per_100g'
        ]
        read_only_fields = ['id']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with protein goals"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'daily_protein_goal', 
            'weight', 'activity_level'
        ]

class FoodEntrySerializer(serializers.ModelSerializer):
    """Serializer for individual food entries"""
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FoodEntry
        fields = [
            'id', 'food_item', 'food_item_id', 'amount_grams',
            'protein_consumed', 'calories_consumed', 'meal_type',
            'created_at'
        ]
        read_only_fields = ['id', 'protein_consumed', 'calories_consumed']

class DailyIntakeSerializer(serializers.ModelSerializer):
    """Serializer for daily intake summaries"""
    entries = FoodEntrySerializer(many=True, read_only=True)
    protein_percentage = serializers.ReadOnlyField()
    protein_goal = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyIntake
        fields = [
            'id', 'date', 'total_protein', 'total_calories',
            'protein_percentage', 'protein_goal', 'entries'
        ]
        read_only_fields = ['id', 'total_protein', 'total_calories']
    
    def get_protein_goal(self, obj):
        """Get user's daily protein goal"""
        if hasattr(obj.user, 'userprofile'):
            return obj.user.userprofile.daily_protein_goal
        return 50.0

class FavoriteFoodSerializer(serializers.ModelSerializer):
    """Serializer for favorite foods"""
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FavoriteFood
        fields = [
            'id', 'food_item', 'food_item_id', 
            'default_amount', 'created_at'
        ]
        read_only_fields = ['id']
