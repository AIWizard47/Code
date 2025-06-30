from django.urls import path
from . import views

urlpatterns = [
    path("registrations/",views.register_views,name="register"),
]
