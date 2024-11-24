from . import views
from django.urls import path


urlpatterns = [
    path("register/",views.register, name="register"),
    path("login/", views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path("",views.home, name = "home"),
    path("createFolder/",views.create_folder, name="createFolder"),
    path("sheetFolder/<int:folder_id>/",views.music_sheet_folder, name="sheetFolder"),
    path("addSheettoFolder/<int:folder_id>/",views.add_sheets_to_folder,name="addSheettoFolder"),
    path("removeSheettoFolder/<int:sheet_id>/",views.remove_sheets_to_folder,name="removeSheettoFolder"),
    path("deleteFolder/<int:folder_id>/",views.delete_folder,name="deleteFolder"),
    path("renameFolder/<int:folder_id>/",views.rename_folder,name="renameFolder"),
    path("folderList/",views.folderList, name="folderList"),
    path("createSheet/",views.create_sheet, name="createSheet"),
    path("deleteSheet/<int:sheet_id>/",views.delete_sheet, name="deleteSheet"),
    path('editSheet/<int:sheet_id>/', views.editSheet, name='editSheet'),
    path('sheet/', views.sheet, name='sheet'),
    path('empty_sheet/', views.create_music_sheet, name='create_music_sheet'),
    ]