"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.metrics import metrics_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/base/', include('base.urls')),
    path('api/company/', include('company.urls')),
    path('api/users/', include('users.urls')),
    path('api/category/', include('category.urls')),
    path('api/ads/', include('ads.urls')),
    path('api/bids/', include('bids.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/category-subscriptions/', include('category_subscriptions.urls')),
    path('api/pricing/', include('pricing.urls')),
    path('api/payments/', include('payments.urls')),
    # Prometheus metrics endpoint (keep unprotected internally; secure via network controls)
    path('metrics', metrics_view, name='metrics'),
    path('', include('django_prometheus.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
