from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("register/",views.register, name="register"),
    path("login/", views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('verify-reset/<str:token>/', views.verify_reset, name='verify_reset'),
    path("",views.home, name = "home"),
    path('profile/', views.profile_view, name='profile'),
    path("createFolder/",views.create_folder, name="createFolder"),
    path("sheetFolder/<int:folder_id>/",views.music_sheet_folder, name="sheetFolder"),
    path("addSheettoFolder/<int:folder_id>/",views.add_sheets_to_folder,name="addSheettoFolder"),
    path("removeSheettoFolder/<int:sheet_id>/<int:folder_id>/",views.remove_sheets_to_folder,name="removeSheettoFolder"),
    path("deleteFolder/<int:folder_id>/",views.delete_folder,name="deleteFolder"),
    path("renameFolder/<int:folder_id>/",views.rename_folder,name="renameFolder"),
    path('shareFolder/<int:folder_id>/', views.share_folder_to_user, name='shareFolder'),
    path('removeFolderPermission/<int:folder_id>/', views.remove_folder_permission, name='removeFolderPermission'),
    path("folderList/",views.folderList, name="folderList"),
    path("createSheet/",views.create_sheet, name="createSheet"),
    path("deleteSheet/<int:sheet_id>/",views.delete_sheet, name="deleteSheet"),
    path('renameSheet/<int:sheet_id>/', views.renameSheet, name='renameSheet'),
    path('shareSheet/<int:sheet_id>/', views.share_sheet_to_user, name='shareSheet'),
    path('removeSheetPermission/<int:sheet_id>/', views.remove_sheet_permission, name='removeSheetPermission'),
    path('search/', views.search_sheet_folder, name='search'),
    path('filter/', views.filter_music_sheets, name='filter'),
    path('createLibrary/', views.create_library, name='createLibrary'),
    path("deleteLibrary/<int:library_id>/",views.delete_library, name="deleteLibrary"),
    path('renameLibrary/<int:library_id>/', views.rename_library, name='renameLibrary'),
    path('updateLibrary/<int:library_id>/', views.update_library, name='updateLibrary'),
    path('sheet/<str:sheet_title>/', views.edit_sheet, name='edit_sheet'),
    path('api/save_sheet/<int:sheet_id>/', views.save_sheet, name='save_sheet'),
    path('api/load_sheet/<int:sheet_id>/', views.load_sheet, name='load_sheet'),
    path('api/save_lyrics/<int:sheet_id>/', views.save_lyrics, name='save_lyrics'),
    path('api/load_lyrics/<int:sheet_id>/', views.load_lyrics, name='load_lyrics'),
    path('api/update_lyrics/<int:sheet_id>/<int:lyrics_id>/', views.update_lyrics, name='update_lyrics'),
    path('api/delete_lyrics/<int:sheet_id>/<int:lyrics_id>/', views.delete_lyrics, name='delete_lyrics'),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)