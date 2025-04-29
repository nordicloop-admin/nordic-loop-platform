from django.db import models
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    """
    Hierarchical categories for waste materials.

    This model supports a tree structure where categories can have parent-child relationships.
    For example, "Plastic" could be a parent category with child categories like
    "PET", "HDPE", "PVC", etc.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly name")
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name (e.g., 'fa-recycle')")
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = ('name', 'parent')

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])

    def get_ancestors(self):
        """Get all ancestors of this category"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendants of this category"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def is_root(self):
        """Check if this category is a root category (has no parent)"""
        return self.parent is None

    def is_leaf(self):
        """Check if this category is a leaf category (has no children)"""
        return self.children.count() == 0

    def get_hierarchy_level(self):
        """Get the level of this category in the hierarchy (0 for root)"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level

