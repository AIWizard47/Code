from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_code, name='submit_code'),
    path('run/', views.run, name='run'),
    path('history/', views.submission_history, name='submission_history'),
    path("submit_contest_code/", views.submit_contest_code, name="submit_contest_code"),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
