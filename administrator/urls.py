from django.urls import path
from . import views
urlpatterns = [
    # Add your URL patterns here
    path('dashboard/',views.home , name='admin-dashboard'),
    path('upload_problem/', views.upload_problem, name='upload_problem'),
    path('upload_testcase/', views.upload_testcase, name='upload_testcase'),
]