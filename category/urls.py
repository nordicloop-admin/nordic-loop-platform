from django.urls import path
from category.views import CategoryView, SubCategoryView,SubCategoryByCategoryView

urlpatterns = [
    path("create/", CategoryView.as_view(), name="create-category"),  
    path("categories/<int:category_id>/", CategoryView.as_view(), name="update-category"), 
    path("", CategoryView.as_view(), name="list-categories"),  
    path("categories/<int:category_id>/delete/", CategoryView.as_view(), name="delete-category"),  



    # subcategories
    path("subcategories/create/", SubCategoryView.as_view(), name="create-subcategory"),  
    path("subcategories/<int:id>/", SubCategoryView.as_view(), name="update-subcategory"),  
    path("subcategories/<int:id>/delete/", SubCategoryView.as_view(), name="delete-subcategory"),
    path("subcategory/<str:category_name>/", SubCategoryByCategoryView.as_view(), name="get-subcategories-by-category"),  
    path("all/", SubCategoryView.as_view(), name="list-subcategories"),
]
