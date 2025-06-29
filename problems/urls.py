from django.urls import path
from . import views

urlpatterns = [
    path('', views.problem_list, name='problem_list'),
    path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'),
]
