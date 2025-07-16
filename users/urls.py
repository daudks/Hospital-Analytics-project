# users/urls.py
from django.urls import path
from .views import profile_view, register, dashboard, home
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('', home, name='home'),  # Adjust as needed
    path('logout/', auth_views.LogoutView.as_view(),
         name='logout'),  
]
# Note: Ensure that the views (profile_view, register, dashboard, home) are defined in users/views.py
# and that the templates for these views exist in the appropriate directory (e.g., users/templates/users/).
