from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum
from datetime import date, timedelta
import logging

from .models import FoodItem, UserProfile, DailyIntake, FoodEntry, FavoriteFood
from .serializers import (
    FoodItemSerializer, UserProfileSerializer, DailyIntakeSerializer,
    FoodEntrySerializer, FavoriteFoodSerializer
)
from .services import FoodAPIService, FoodCacheService

logger = logging.getLogger(__name__)


# Add this import at the top
from .services import FoodAPIService, FoodCacheService

# Update the FoodSearchView class
class FoodSearchView(generics.ListAPIView):
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if len(query) < 2:
            return FoodItem.objects.none()
        
        # Search local database first
        local_results = FoodItem.objects.filter(
            name__icontains=query
        )[:10]
        
        # If less than 5 local results, search external API
        if local_results.count() < 5:
            food_service = FoodAPIService()
            api_results = food_service.search_foods(query, limit=10)
            
            # Cache new foods in database
            for food_data in api_results:
                try:
                    FoodCacheService.get_or_create_food_item(food_data)
                except Exception as e:
                    logger.error(f"Error caching food item: {e}")
        
        # Return updated local results
        return FoodItem.objects.filter(name__icontains=query)[:20]
