from django.shortcuts import render
import pyrebase

# config = {
#     "apiKey": "AIzaSyAFdTQIkXeJCkE760kQH1kZtCjkZnm3o7Q",
#     "authDomain": "hellomusic-63ee9.firebaseapp.com",
#     "databaseURL": "https://hellomusic-63ee9-default-rtdb.firebaseio.com",
#     "projectId": "hellomusic-63ee9",
#     "storageBucket": "hellomusic-63ee9.firebasestorage.app",
#     "messagingSenderId": "186714219968",
#     "appId": "1:186714219968:web:456d77546cc2cc3b73d425",
# }

# firebase = pyrebase .initialize_app(config)
# authe = firebase.auth()
# database = firebase.database()

def home(request):
#     music_sheets = database.child('MusicSheet').get().each()
    
#    # Filter out any empty items
#     valid_music_sheets = [sheet for sheet in music_sheets if sheet.val()]
    context = {
        # "music_sheets": valid_music_sheets
    }
    return render(request,"HelloMusicApp/index.html",context)


def folder(request):
    context={}
    return render(request,"HelloMusicApp/folder.html",context)

def folderList(request):
    context={
          "range_list": range(12), 
    }
    return render(request,"HelloMusicApp/folderList.html",context)

