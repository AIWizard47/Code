"""
URL configuration for CodePlatform project.

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
from users import views

urlpatterns = [
    path('sam/admin/', admin.site.urls),
    path('administrator/',include('administrator.urls')),
    path("",include("base.urls")),
    path("problems/",include("problems.urls")),
    path("submissions/",include("submissions.urls")),
    # path("user/",include("users.urls"))
    path('accounts/', include('django.contrib.auth.urls')),
    path('account/',include("users.urls")),
    path('duels/', include('players.urls')),  # Added for duels
    path("profile/<str:username>/", views.user_profile, name="user_profile"),
    path('profile-edit/edit-form/', views.profile_edit_form, name='profile_edit_form'),
    path('profile-edit/edit/', views.profile_edit_save, name='profile_edit_save'),
]
