from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
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
            return redirect('/login/')
    else:
        form = UserCreationForm()
    
    return render(request, 'HelloMusicApp/register.html', {'form': form})

def home(request):   
   
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    music_sheets_list = user_music_sheets_list(request)
 
    
    context = {
        'music_sheets': music_sheets_list,
        'form': addSheetform
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

@require_POST
def create_sheet(request): #need to login before create
    
    form = MusicSheetForm(request.POST)
    
    if form.is_valid():
        music_sheet = form.save() #direct save into database

        UserMusicSheet.objects.create(sheet=music_sheet, user=request.user)
            
    return redirect('/')



def user_music_sheets_list(request): #need to login before show it
 return MusicSheet.objects.filter(users=request.user)


@require_POST
def delete_sheet(request, sheet_id): #need to login and have sheet before delete it

    try:    
        # Use get_object_or_404 to find the music sheet by ID
        music_sheet = get_object_or_404(MusicSheet, ID=sheet_id)    
        music_sheet.delete()
        return JsonResponse({'success': True})
    except MusicSheet.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Music sheet not found'})

    # For example, if you want to check if the sheet belongs to the user, you can do:
    # if music_sheet.user != request.user:
    #     return JsonResponse({'success': False, 'error': 'Not authorized to delete this sheet'})
    
@require_POST
def editSheet(request, sheet_id):
    
    new_title = request.POST.get('title', '').strip()    
    
    if not new_title:
        return JsonResponse({'success': False, 'error': 'Title cannot be empty'})
    
    # Use get_object_or_404 to find the music sheet by ID
    music_sheet = get_object_or_404(MusicSheet, ID=sheet_id)    
    
    # Update the title and save it
    music_sheet.title = new_title
    music_sheet.save()

    return JsonResponse({'success': True, 'title': new_title})

    # Check if the user is authorized to edit this music sheet (optional)
    # if music_sheet.user != request.user:
    #     return JsonResponse({'success': False, 'error': 'Not authorized to edit this sheet'})





