from django.urls import path
from ads.views import AdView

urlpatterns = [
    path("create/", AdView.as_view(), name="create-ad"),
    path("", AdView.as_view(), name="list-ads"),
    path("<int:ad_id>/", AdView.as_view(), name="update-ad"),
    path("<int:ad_id>/delete/", AdView.as_view(), name="delete-ad"),
]
