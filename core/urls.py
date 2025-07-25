"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from users import views as user_views
from analytics import views as analytics_views
from django.views.generic import RedirectView

# Import the profile_view function directly
from users.views import profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
    path('users/', include('users.urls')),
    path('', user_views.home, name='home'),  # Home page
    path('register/', user_views.register, name='register'),  # Registration page
    path('dashboard/', user_views.dashboard, name='dashboard'),  # User dashboard
    path('accounts/profile/', profile_view, name='profile'),  # User profile page
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),  # Favicon
    path('accounts/', include('django.contrib.auth.urls')),  # ✅ Add this line
    # This includes login, logout, password change, and password reset URLs                     
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
