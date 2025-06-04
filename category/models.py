from django.db import models

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

    Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    color = models.CharField(max_length=50, choices=MATERIAL_COLOR_CHOICES, blank=True, null=True)
    material_grade = models.CharField(max_length=255, blank=True, null=True)
    material_form = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.Category

