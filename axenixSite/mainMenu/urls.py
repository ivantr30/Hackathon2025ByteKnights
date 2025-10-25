from django.urls import path
from . import views

app_name = 'mainMenu'

urlpatterns = [
    path("", views.main_view, name="room_list"),

    path("join/", views.join_page, name="join_page"),
    path("register/", views.reg_page, name="register_page"),
    
    path("api/login/", views.run_function_join, name="api_login"),
    path("api/register/", views.register_user, name="api_register"),
    
    path("room/<slug:slug>/", views.room_view, name="room_detail"),
]