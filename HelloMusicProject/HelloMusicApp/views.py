from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
# import pyrebase

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

def register(request):
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST) #django register form
        if form.is_valid():
            form.save() 
            messages.success(request, "User created successfully.")
            return redirect('login/')
    else:
        form = UserCreationForm()
    
    return render(request, 'HelloMusicApp/register.html', {'form': form})

def home(request):
    music_sheets_list = user_music_sheets_list(request)
    
    context = {
        'music_sheets': music_sheets_list
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


def create_sheet(request): #need to login before create
    
    if request.method == 'POST':
        form = MusicSheetForm(request.POST)
        if form.is_valid():
            music_sheet = form.save() #direct save into database

            UserMusicSheet.objects.create(sheet=music_sheet, user=request.user)
            
            return redirect('/')

    else:
        form = MusicSheetForm()
        
    context={
        'form': form
    }
    
    return render(request, 'HelloMusicApp/createSheet.html', context)


def user_music_sheets_list(request): #need to login before show it
 return MusicSheet.objects.filter(users=request.user)

@require_POST
def delete_sheet(request,sheet_id):
    try:
        # Find the music sheet by ID and delete it
        music_sheet = MusicSheet.objects.get(ID=sheet_id)
        music_sheet.delete()
        return JsonResponse({'success': True})
    except MusicSheet.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Music sheet not found'})
 

