from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login as auth_login  # Rename the login method to avoid conflict
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.timezone import localtime, now
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.http import require_http_methods


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

        try:
            # First check if user exists
            user = User.objects.get(email=email)
            
            # Try authentication
            auth_user = authenticate(request, email=email, password=password)
            if auth_user is not None:
                auth_login(request, auth_user)
                return redirect('home')
            else:
                # Try to authenticate with the backend directly
                from HelloMusicApp.backends import EmailBackend
                backend = EmailBackend()
                direct_auth = backend.authenticate(request, email=email, password=password)
                
                messages.error(request, 'Invalid credentials, please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'Invalid credentials, please try again.')
        except Exception as e:
            messages.error(request, 'An error occurred during login.')
            
    return render(request, 'HelloMusicApp/login.html')

def request_password_reset(request):    
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        try:
            user = User.objects.get(email=email)
            
            if password == confirm_password:
                token = get_random_string(64)
                
                # Create token record
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=timezone.now() + timedelta(hours=24),
                    new_password=password
                )
                
                reset_url = f"{request.scheme}://{request.get_host()}/verify-reset/{token}/"
                
                # Send email
                try:
                    send_mail(
                        'Password Reset Verification - HelloMusic',
                        '',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        html_message=render_to_string('HelloMusicApp/reset_email.html', {
                            'user': user,
                            'reset_url': reset_url,
                        }),
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.error(request, "Error sending email. Please try again.")
                    return redirect('request_password_reset')
                
                messages.success(request, "Please check your email to verify your password reset request.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        except User.DoesNotExist:
            messages.error(request, "No user found with this email address.")
    
    return render(request, 'HelloMusicApp/request_reset.html')

@require_http_methods(["GET"])
def verify_reset(request, token):    
    try:
        # Query the token and print result
        reset_token = PasswordResetToken.objects.filter(
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if reset_token is None:
            print("DEBUG: No valid token found")
            messages.error(request, "Invalid or expired reset link.")
            return redirect('request_password_reset')
        
        # Get user and update password
        user = reset_token.user
        new_password = reset_token.new_password
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        messages.success(request, "Your password has been reset successfully.")
        return redirect('login')
        
    except Exception as e:
        messages.error(request, "An error occurred during password reset.")
        return redirect('request_password_reset')
    
def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('login')

def home(request):   
   
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    music_sheets_list = user_music_sheets_list(request)
    recent_folder_list =  UserMusicSheetFolder.objects.filter(user=request.user).order_by('-last_accessed')[:4].select_related('folder')
    
    
    context = {
        'music_sheets': music_sheets_list,
        'recent_sheet_folder': recent_folder_list,
        'sheetform': addSheetform,
        'folderform': addFolderform
    }
    
    return render(request,"HelloMusicApp/index.html",context)


# Music sheet management
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

# Music sheet folder management
@require_POST
def create_folder(request): #need to login before create
    
    form = MusicSheetFolderForm(request.POST)
    
    if form.is_valid():
        music_sheet_folder = form.save() 
           
        UserMusicSheetFolder.objects.create(
            folder=music_sheet_folder,
            user=request.user,
            last_accessed= localtime(),
            role='Owner' 
        )
            
    return redirect('/folderList/')


def user_folder(request):
    return MusicSheetFolder.objects.filter(users=request.user)
   
   
def music_sheet_folder(request,folder_id):
    folder = get_object_or_404(MusicSheetFolder, ID=folder_id, users=request.user)
    folder_music_sheets = folder.music_sheets.all()
    recent_folder_list =  UserMusicSheetFolder.objects.filter(user=request.user).order_by('-last_accessed')[:4].select_related('folder')
    music_sheets_list = user_music_sheets_list(request) 
    folder_access = get_object_or_404(UserMusicSheetFolder, folder=folder_id, user=request.user)
    
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    addsheetfolderform = AddSheetsToFolderForm(initial={'selected_sheets': music_sheets_list})
    
    folder_access.update_access_time()
  
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheetfolderform': addsheetfolderform,
        'recent_sheet_folder': recent_folder_list,
        'folder_music_sheets': folder_music_sheets,
        'folder' : folder,
        'music_sheets' : music_sheets_list,            
    }
    return render(request,"HelloMusicApp/folder.html",context)

def folderList(request):
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    user_folder_list = user_folder(request)
    recent_folder_list =  UserMusicSheetFolder.objects.filter(user=request.user).order_by('-last_accessed')[:4].select_related('folder')
    
    
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheet_folder': user_folder_list,    
        'recent_sheet_folder': recent_folder_list,   
    }
    
    return render(request,"HelloMusicApp/folderList.html",context)

@require_POST
def add_sheets_to_folder(request, folder_id):
    folder = get_object_or_404(MusicSheetFolder, ID=folder_id, users=request.user)
    folder_access = get_object_or_404(UserMusicSheetFolder, folder=folder_id, user=request.user)
        
    form = AddSheetsToFolderForm(request.POST)
    
    if form.is_valid():
         selected_sheets = form.cleaned_data['selected_sheets']
         for sheet in selected_sheets:
            sheet.folder = folder
            sheet.save()
            
    folder_access.update_access_time()
    
    return redirect("sheetFolder", folder_id=folder_id)

@require_POST
def remove_sheets_to_folder(request, sheet_id,folder_id):
    music_sheet = get_object_or_404(MusicSheet, ID=sheet_id, users=request.user)   
   
    folder_access = get_object_or_404(UserMusicSheetFolder, folder=folder_id, user=request.user)
    
    music_sheet.folder = None
    music_sheet.save()
    
    folder_access.update_access_time()

    return JsonResponse({'success': True})

@require_POST
def delete_folder(request, folder_id): 

    try:    
        # Use get_object_or_404 to find the music sheet by ID   
        folder = get_object_or_404(MusicSheetFolder, ID=folder_id)    
        
        music_sheet = MusicSheet.objects.filter(folder=folder)
     
        music_sheet.delete()
        
        folder.delete()
        
        return JsonResponse({'success': True})
    except MusicSheetFolder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Folder not found'})

    # For example, if you want to check if the sheet belongs to the user, you can do:
    # if music_sheet.user != request.user:
    #     return JsonResponse({'success': False, 'error': 'Not authorized to delete this sheet'})


@require_POST
def rename_folder(request, folder_id):
    
    new_name = request.POST.get('name', '').strip()    
    
    if not new_name:
        return JsonResponse({'success': False, 'error': 'Title cannot be empty'})
    
    folder = get_object_or_404(MusicSheetFolder, ID=folder_id)    
    
    folder.name = new_name
    folder.save()

    return JsonResponse({'success': True})

# Music Notation Management
def sheet(request):
    context = {}
    return render(request,"HelloMusicApp/sheet.html",context)

    
def create_music_sheet(request):
    return render(request, 'HelloMusicApp/empty_sheet.html')



