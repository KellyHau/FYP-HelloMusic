from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login as auth_login  # Rename the login method to avoid conflict
from django.contrib import messages
from django.contrib.auth import logout


def register(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save() 
            messages.success(request, "User created successfully.")
            return redirect('/login/')
    else:
        form = RegisterForm()
    
    return render(request, 'HelloMusicApp/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if the user is authenticated
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            auth_login(request, user)  # Log the user in if authentication is successful
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials, please try again.')
            return render(request, 'HelloMusicApp/login.html')

    return render(request, 'HelloMusicApp/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('login')

def home(request):   
   
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    music_sheets_list = user_music_sheets_list(request)
    user_folder_list = user_folder(request)
 
    
    context = {
        'music_sheets': music_sheets_list,
        'sheet_folder': user_folder_list,
        'sheetform': addSheetform,
        'folderform': addFolderform
    }
    
    return render(request,"HelloMusicApp/index.html",context)


@require_POST
def create_folder(request): #need to login before create
    
    form = MusicSheetFolderForm(request.POST)
    
    if form.is_valid():
        music_sheet_folder = form.save() 
           
        UserMusicSheetFolder.objects.create(
            folder=music_sheet_folder,
            user=request.user,
            role='Owner' 
        )
            
    return redirect('/')


def user_folder(request):
    return MusicSheetFolder.objects.filter(users=request.user)
   
   
def music_sheet_folder(request,folder_id):
    folder = get_object_or_404(MusicSheetFolder, ID=folder_id, users=request.user)
    music_sheets = folder.music_sheets.all()
    folder_name  = folder.name
    
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    user_folder_list = user_folder(request)
    
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheet_folder': user_folder_list,
        'music_sheets': music_sheets,
        'folder_name' : folder_name,
            
    }
    return render(request,"HelloMusicApp/folder.html",context)

def folderList(request):
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    user_folder_list = user_folder(request)
    
    
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheet_folder': user_folder_list,       
    }
    
    return render(request,"HelloMusicApp/folderList.html",context)

@require_POST
def create_sheet(request): #need to login before create
    
    form = MusicSheetForm(request.POST)
    
    if form.is_valid():
      
        music_sheet = form.save() 
           
        UserMusicSheet.objects.create(
            sheet=music_sheet,
            user=request.user,
            role='Owner' 
        )
            
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

def sheet(request):
    context = {}
    return render(request,"HelloMusicApp/sheet.html",context)




