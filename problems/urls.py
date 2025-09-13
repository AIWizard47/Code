from django.urls import path
from . import views

urlpatterns = [
    path('', views.problem_list, name='problem_list'),
    path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'),
    path('contests/', views.contest_list, name='contest_list'),
    path('contests/<int:pk>/', views.contest_detail, name='contest_detail'),
    path('contests/<int:pk>/leaderboard/', views.contest_leaderboard, name='contest_leaderboard'),
    path('contests/<int:pk>/register/', views.register_for_contest, name='register_for_contest'),
    path("logout/",views.logout_view,name="logout"),
    path('contests/<int:contest_id>/problem/<int:problem_id>/',views.contest_problem_detail,name='contest_problem_detail'),
    path("problem/<slug:slug>/generate/", views.generate_problem_variation, name="generate_problem_variation"),

]
