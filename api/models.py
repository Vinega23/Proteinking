from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class FoodItem(models.Model):
    """Food items from external API with cached nutritional data"""
    fdc_id = models.CharField(max_length=20, unique=True, help_text="FDC ID from USDA API")
    name = models.CharField(max_length=200)
    brand_owner = models.CharField(max_length=200, blank=True, null=True)
    protein_per_100g = models.FloatField(validators=[MinValueValidator(0)])
    calories_per_100g = models.FloatField(validators=[MinValueValidator(0)])
    carbs_per_100g = models.FloatField(validators=[MinValueValidator(0)])
    fat_per_100g = models.FloatField(validators=[MinValueValidator(0)])
    fiber_per_100g = models.FloatField(validators=[MinValueValidator(0)], default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.protein_per_100g}g protein/100g)"

class UserProfile(models.Model):
    """Extended user profile for protein tracking goals"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_protein_goal = models.FloatField(
        default=50.0, 
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        help_text="Daily protein goal in grams"
    )
    weight = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        help_text="Body weight in kg"
    )
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary'),
            ('light', 'Light Activity'),
            ('moderate', 'Moderate Activity'),
            ('active', 'Very Active'),
            ('extra_active', 'Extra Active'),
        ],
        default='moderate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.daily_protein_goal}g/day"

class DailyIntake(models.Model):
    """Daily protein intake tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    total_protein = models.FloatField(default=0, validators=[MinValueValidator(0)])
    total_calories = models.FloatField(default=0, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    @property
    def protein_percentage(self):
        """Calculate percentage of daily protein goal achieved"""
        if hasattr(self.user, 'userprofile'):
            goal = self.user.userprofile.daily_protein_goal
            return (self.total_protein / goal * 100) if goal > 0 else 0
        return 0
    
    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.total_protein}g protein"

class FoodEntry(models.Model):
    """Individual food entries for tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    daily_intake = models.ForeignKey(DailyIntake, on_delete=models.CASCADE, related_name='entries')
    
    amount_grams = models.FloatField(validators=[MinValueValidator(0.1)])
    protein_consumed = models.FloatField(validators=[MinValueValidator(0)])
    calories_consumed = models.FloatField(validators=[MinValueValidator(0)])
    
    meal_type = models.CharField(
        max_length=20,
        choices=[
            ('breakfast', 'Breakfast'),
            ('lunch', 'Lunch'),
            ('dinner', 'Dinner'),
            ('snack', 'Snack'),
        ],
        default='snack'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Calculate protein and calories based on amount
        self.protein_consumed = (self.food_item.protein_per_100g * self.amount_grams) / 100
        self.calories_consumed = (self.food_item.calories_per_100g * self.amount_grams) / 100
        super().save(*args, **kwargs)
        
        # Update daily intake totals
        self.daily_intake.total_protein = sum(
            entry.protein_consumed for entry in self.daily_intake.entries.all()
        )
        self.daily_intake.total_calories = sum(
            entry.calories_consumed for entry in self.daily_intake.entries.all()
        )
        self.daily_intake.save()
    
    def __str__(self):
        return f"{self.food_item.name} - {self.amount_grams}g ({self.protein_consumed:.1f}g protein)"

class FavoriteFood(models.Model):
    """User's favorite foods for quick access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    default_amount = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Default serving size in grams"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'food_item']
        ordering = ['food_item__name']
    
    def __str__(self):
        return f"{self.user.username} - {self.food_item.name}"

