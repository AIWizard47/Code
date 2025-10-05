from django.urls import path
from . import views

urlpatterns = [
    path('find-match', views.find_match, name='find_match'),
    path('accept-duel/<int:duel_id>/', views.accept_duel, name='accept_duel'),
    path('duel-room/<int:match_id>/', views.duel_room, name='duel_room'),
    path("room/<int:match_id>/", views.match_room, name="match_room"),
    path("check-match/", views.check_for_match, name="check_for_match"),  # 🔹 Add this
]
