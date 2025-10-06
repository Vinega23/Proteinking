import requests
from typing import List, Dict, Optional
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)

class FoodAPIService:
    """Service class for interacting with USDA FoodData Central API"""
    
    def __init__(self):
        self.base_url = "https://api.nal.usda.gov/fdc/v1/"
        self.api_key = config('USDA_API_KEY', default='')
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
        })
    
    def search_foods(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for foods using USDA API
        
        Args:
            query: Search term for food items
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries containing food data
        """
        if len(query.strip()) < 2:
            return []
        
        url = f"{self.base_url}foods/search"
        params = {
            'query': query,
            'pageSize': limit,
            'dataType': ['Foundation', 'SR Legacy'],  # High-quality data sources
            'sortBy': 'dataType.keyword',
            'sortOrder': 'asc'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            foods = data.get('foods', [])
            
            # Transform API data to our model format
            formatted_foods = []
            for food in foods:
                formatted_food = self._format_food_data(food)
                if formatted_food:
                    formatted_foods.append(formatted_food)
            
            return formatted_foods
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching foods: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in food search: {e}")
            return []
    
    def get_food_details(self, fdc_id: str) -> Optional[Dict]:
        """
        Get detailed nutrition information for a specific food
        
        Args:
            fdc_id: FDC ID of the food item
            
        Returns:
            Dictionary with detailed food data or None
        """
        url = f"{self.base_url}food/{fdc_id}"
        params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            food_data = response.json()
            return self._format_food_data(food_data, detailed=True)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting food details for {fdc_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting food details: {e}")
            return None
    
    def _format_food_data(self, food_data: Dict, detailed: bool = False) -> Optional[Dict]:
        """
        Format API response data to match our FoodItem model
        
        Args:
            food_data: Raw API response data
            detailed: Whether this is from detailed API call
            
        Returns:
            Formatted dictionary or None if invalid data
        """
        try:
            # Extract basic information
            fdc_id = str(food_data.get('fdcId', ''))
            name = food_data.get('description', '').title()
            brand_owner = food_data.get('brandOwner', '')
            
            if not fdc_id or not name:
                return None
            
            # Extract nutrients
            nutrients = {}
            food_nutrients = food_data.get('foodNutrients', [])
            
            # Nutrient ID mappings from USDA database
            nutrient_mapping = {
                '1003': 'protein',      # Protein
                '1008': 'calories',     # Energy (kcal)
                '1005': 'carbs',        # Carbohydrate, by difference
                '1004': 'fat',          # Total lipid (fat)
                '1079': 'fiber',        # Fiber, total dietary
            }
            
            for nutrient in food_nutrients:
                nutrient_id = str(nutrient.get('nutrient', {}).get('id', ''))
                if nutrient_id in nutrient_mapping:
                    nutrient_name = nutrient_mapping[nutrient_id]
                    amount = nutrient.get('amount', 0)
                    
                    # Convert to per 100g if needed
                    unit = nutrient.get('nutrient', {}).get('unitName', '').upper()
                    if unit == 'KCAL' and nutrient_name == 'calories':
                        nutrients[nutrient_name] = float(amount or 0)
                    elif unit == 'G':  # Grams
                        nutrients[nutrient_name] = float(amount or 0)
            
            # Ensure all required nutrients have values
            formatted_data = {
                'fdc_id': fdc_id,
                'name': name[:200],  # Truncate to model max_length
                'brand_owner': brand_owner[:200] if brand_owner else '',
                'protein_per_100g': nutrients.get('protein', 0.0),
                'calories_per_100g': nutrients.get('calories', 0.0),
                'carbs_per_100g': nutrients.get('carbs', 0.0),
                'fat_per_100g': nutrients.get('fat', 0.0),
                'fiber_per_100g': nutrients.get('fiber', 0.0),
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting food data: {e}")
            return None

class FoodCacheService:
    """Service for caching and retrieving food data"""
    
    @staticmethod
    def get_or_create_food_item(food_data: Dict):
        """
        Get existing food item or create new one from API data
        
        Args:
            food_data: Formatted food data dictionary
            
        Returns:
            Tuple of (FoodItem instance, created boolean)
        """
        from .models import FoodItem
        
        try:
            food_item, created = FoodItem.objects.get_or_create(
                fdc_id=food_data['fdc_id'],
                defaults={
                    'name': food_data['name'],
                    'brand_owner': food_data['brand_owner'],
                    'protein_per_100g': food_data['protein_per_100g'],
                    'calories_per_100g': food_data['calories_per_100g'],
                    'carbs_per_100g': food_data['carbs_per_100g'],
                    'fat_per_100g': food_data['fat_per_100g'],
                    'fiber_per_100g': food_data['fiber_per_100g'],
                }
            )
            
            # Update existing item if data has changed
            if not created:
                updated = False
                for field, value in food_data.items():
                    if field != 'fdc_id' and getattr(food_item, field) != value:
                        setattr(food_item, field, value)
                        updated = True
                
                if updated:
                    food_item.save()
            
            return food_item, created
            
        except Exception as e:
            logger.error(f"Error creating/updating food item: {e}")
            raise
