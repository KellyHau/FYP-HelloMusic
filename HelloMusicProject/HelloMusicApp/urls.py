from . import views
from django.urls import path
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("register/",views.register, name="register"),
    path("login/", LoginView.as_view(template_name='HelloMusicApp/login.html'), name='login'),
    path("logout/", LogoutView.as_view(), name='logout'),
    path("",views.home, name = "home"),
    path("folder/",views.folder, name="folder"),
    path("folderList/",views.folderList, name="folderList"),
    path("createSheet/",views.create_sheet, name="createSheet"),
    path("deleteSheet/<int:sheet_id>/",views.delete_sheet, name="deleteSheet"),
    path('editSheet/<int:sheet_id>/', views.editSheet, name='editSheet'),
    ]