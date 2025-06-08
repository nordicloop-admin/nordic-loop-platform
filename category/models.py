from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CategorySpecification(models.Model):
    MATERIAL_COLOR_CHOICES = [
        ("Natural/Clear", "Natural/Clear"),
        ("White", "White"),
        ("Black", "Black"),
        ("Red", "Red"),
        ("Blue", "Blue"),
        ("Green", "Green"),
        ("Yellow", "Yellow"),
        ("Orange", "Orange"),
        ("Purple", "Purple"),
        ("Brown", "Brown"),
        ("Gray", "Gray"),
        ("Mixed Colors", "Mixed Colors"),
        ("Custom Color", "Custom Color"),
    ]

    MATERIAL_GRADE_CHOICES = [
        ("virgin_grade", "Virgin Grade"),
        ("industrial_grade", "Industrial Grade"),
        ("food_grade", "Food Grade"),
        ("medical_grade", "Medical Grade"),
        ("automotive_grade", "Automotive Grade"),
        ("electrical_grade", "Electrical Grade"),
        ("recycled_grade", "Recycled Grade"),
    ]

    MATERIAL_FORM_CHOICES = [
        ("pellets_granules", "Pellets/Granules"),
        ("flakes", "Flakes"),
        ("regrind", "Regrind"),
        ("sheets", "Sheets"),
        ("film", "Film"),
        ("parts_components", "Parts/Components"),
        ("powder", "Powder"),
        ("fiber", "Fiber"),
    ]

    Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='specifications')
    color = models.CharField(max_length=50, choices=MATERIAL_COLOR_CHOICES, blank=True, null=True)
    material_grade = models.CharField(max_length=50, choices=MATERIAL_GRADE_CHOICES, blank=True, null=True)
    material_form = models.CharField(max_length=50, choices=MATERIAL_FORM_CHOICES, blank=True, null=True)
    additional_specifications = models.TextField(
        blank=True, 
        null=True, 
        help_text="e.g., Melt Flow Index: 2.5, Density: 0.95 g/cm³"
    )

    class Meta:
        verbose_name = "Category Specification"
        verbose_name_plural = "Category Specifications"
        unique_together = ['Category', 'color', 'material_grade', 'material_form']

    def __str__(self):
        parts = [self.Category.name]
        if self.material_grade:
            parts.append(self.get_material_grade_display())
        if self.color:
            parts.append(self.color)
        if self.material_form:
            parts.append(self.get_material_form_display())
        return " - ".join(parts)

    def clean(self):
        """Custom validation for CategorySpecification"""
        super().clean()
        
        # At least one specification field should be provided
        if not any([self.color, self.material_grade, self.material_form, self.additional_specifications]):
            raise ValidationError(
                "At least one specification field (color, material grade, material form, or additional specifications) must be provided."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

