import json
from django import template
from django.shortcuts import render, redirect
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login as auth_login  # Rename the login method to avoid conflict
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.timezone import localtime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError, transaction
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Q
import os
from django.template import loader, TemplateDoesNotExist


def register(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user) 
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
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    context = {
        'music_sheets': music_sheets_list,
        'recent_sheet_folder': recent_folder_list,
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'profile': profile
    }
    
    return render(request,"HelloMusicApp/index.html",context)

def profile_view(request):
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user, 
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user, user=request.user)
    
    return render(request, 'HelloMusicApp/profile.html', {
        'form': form,
        'profile': profile
    })

# Music sheet management
@require_POST
def create_sheet(request):
    
    form = MusicSheetForm(request.POST, user=request.user)
    
 
    if form.is_valid():
          
        music_sheet = form.save() 
                    
        UserMusicSheet.objects.create(
            sheet=music_sheet,
            user=request.user,
            role='owner'
        )
        
        return redirect('/')
 

def user_music_sheets_list(request): 
 return MusicSheet.objects.filter(users=request.user)


@require_POST
def delete_sheet(request, sheet_id): 

    try:    
        music_sheet = get_object_or_404(MusicSheet, ID=sheet_id)    
        
        user_role = UserMusicSheet.objects.filter(sheet=music_sheet, user=request.user, role='owner').first()
        
        if not user_role:
            return JsonResponse({'status': False, 'mes': 'Not authorized to delete this sheet'})

        music_sheet.delete()
        return JsonResponse({'status': True, 'mes': 'Music sheet deleted successfully.'})
    
    except MusicSheet.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Music sheet not found'})
    
@require_POST
def renameSheet(request, sheet_id):
    
    new_title = request.POST.get('title', '').strip()    
    
    music_sheet = get_object_or_404(MusicSheet, ID=sheet_id)    
    
    user_role = UserMusicSheet.objects.filter(sheet=music_sheet, user=request.user, role__in =['owner','editor']).first()
    
    if not user_role:
           return JsonResponse({'status': False, 'mes': 'Not authorized to edit this sheet'})
    
    # Update the title and save it
    music_sheet.title = new_title
    music_sheet.save()

    return JsonResponse({'status': True, 'mes': 'Music sheet rename successfully.'})


def share_sheet_to_user(request, sheet_id):

    if request.method == "POST":
        
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()
        
        try:
            user = get_object_or_404(User, email=email)
            sheet = get_object_or_404(MusicSheet, ID=sheet_id)
         
            UserMusicSheet.objects.update_or_create(
                user=user,
                sheet=sheet,
                role = role,
            )

            # Send email notification
            send_mail(
                "You've been granted access to a music sheet",
                f"You've been granted '{role}' access to the music sheet: {sheet.title}.\n Welcome using Hello Music Application!",
                'hellomusic090@gmail.com',
                [email],
                fail_silently=False,
            )


            return JsonResponse({'status': True, 'mes': f'Successful share to {email}'})
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'mes': 'User not found'})
        except MusicSheet.DoesNotExist:
            return JsonResponse({'status': False, 'mes': 'Music sheet not found'})
    
    if request.method == "GET":
                
        users = UserMusicSheet.objects.filter(sheet=sheet_id).annotate(
        role_priority=Case(
                When(role='owner', then=Value(1)),
                When(role='editor', then=Value(2)),
                When(role='viewer', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by('role_priority')
        
        current_user = UserMusicSheet.objects.filter(user=request.user,sheet=sheet_id).first()
         
        user_list = [
            {
                "email": user.user.username,
                "role": user.role
            }
            for user in users
        ]
         
        data = { 
                "users": user_list,
                "current_role": current_user.role ,
            }
        return JsonResponse(data)
        

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
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    addsheetfolderform = AddSheetsToFolderForm(user=request.user)
    
    folder_access.update_access_time()
  
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheetfolderform': addsheetfolderform,
        'recent_sheet_folder': recent_folder_list,
        'folder_music_sheets': folder_music_sheets,
        'folder' : folder,
        'music_sheets' : music_sheets_list,
        'profile': profile            
    }
    return render(request,"HelloMusicApp/folder.html",context)


def folderList(request):
    addSheetform = MusicSheetForm(initial={'title': 'Untitled Sheet'})
    addFolderform = MusicSheetFolderForm(initial={'name': 'Untitled Folder'})
    user_folder_list = user_folder(request)
    recent_folder_list =  UserMusicSheetFolder.objects.filter(user=request.user).order_by('-last_accessed')[:4].select_related('folder')
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    context={       
        'sheetform': addSheetform,
        'folderform': addFolderform,
        'sheet_folder': user_folder_list,    
        'recent_sheet_folder': recent_folder_list,
        'profile': profile   
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
    
    user_role = UserMusicSheetFolder.objects.filter(folder=folder_id, user=request.user, role__in =['owner','editor']).first()
        
    if not user_role:
            return JsonResponse({'status': False, 'mes': 'Not authorized to remove sheet from folder.'})
    
    
    music_sheet.folder = None
    music_sheet.save()
    
    folder_access.update_access_time()

    return JsonResponse({'status': True,'mes': f'{music_sheet.title} remove from {folder_access.folder.name} successfully.'})

def share_folder_to_user(request, folder_id):

    if request.method == "POST":
        
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()
        
        try:
            user = get_object_or_404(User, email=email)
            folder = get_object_or_404(MusicSheetFolder, ID=folder_id)
         
            with transaction.atomic():
                
                UserMusicSheetFolder.objects.update_or_create(
                    user=user,
                    folder=folder,
                    role=role,
                )

                music_sheets = MusicSheet.objects.filter(folder=folder)
                for sheet in music_sheets:
                    UserMusicSheet.objects.update_or_create(
                        user=user,
                        sheet=sheet,
                        role = role,
                    )

                # Send email notification
                send_mail(
                    "You've been granted access to a Music Sheet Folder",
                    f"You've been granted '{role}' access to the Folder: {folder.name}.\n Welcome using Hello Music Application!",
                    'hellomusic090@gmail.com',
                    [email],
                    fail_silently=False,
                )


            return JsonResponse({'status': True, 'mes': f'Successful share to {email}'})
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'mes': 'User not found'})
        except MusicSheetFolder.DoesNotExist:
            return JsonResponse({'status': False, 'mes': 'Folder not found'})
    
    if request.method == "GET":
                
        users = UserMusicSheetFolder.objects.filter(folder=folder_id).annotate(
        role_priority=Case(
                When(role='owner', then=Value(1)),
                When(role='editor', then=Value(2)),
                When(role='viewer', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by('role_priority')
        
        current_user = UserMusicSheetFolder.objects.filter(user=request.user,folder=folder_id).first()
        
        user_list = [
            {
                "email": user.user.username,
                "role": user.role
            }
            for user in users
        ]
         
        data = { 
                "users": user_list,
                "current_role": current_user.role ,
            }
        return JsonResponse(data)
        

@require_POST
def delete_folder(request, folder_id): 

    try:    
    
        folder = get_object_or_404(MusicSheetFolder, ID=folder_id)    
        
        music_sheet = MusicSheet.objects.filter(folder=folder)
        
        user_role = UserMusicSheetFolder.objects.filter(folder=folder, user=request.user, role='owner').first()
        
        if not user_role:
            return JsonResponse({'status': False, 'mes': 'Not authorized to delete this folder'})

        music_sheet.delete()
        
        folder.delete()
        
        return JsonResponse({'status': True, 'mes': 'Folder deleted successfully.'})
    
    except MusicSheetFolder.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Folder not found'})


@require_POST
def rename_folder(request, folder_id):
    
    try:
    
        new_name = request.POST.get('name', '').strip()    
        
        folder = get_object_or_404(MusicSheetFolder, ID=folder_id)    
        
        user_role = UserMusicSheetFolder.objects.filter(folder=folder, user=request.user, role__in =['owner','editor']).first()
        
        if not user_role:
            return JsonResponse({'status': False, 'mes': 'Not authorized to edit this folder'})
        
        folder.name = new_name
        folder.save()

        return JsonResponse({'success': True, 'mes': 'Folder rename successfully.'})

    except MusicSheetFolder.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Folder not found'})


# Search sheet and folder
def search_sheet_folder(request):
    query = request.GET.get('q', '').strip()  
    if not query:  
        return JsonResponse({'sheets': [], 'folders': []})
    
    sheets = list(
        MusicSheet.objects.filter(Q(title__icontains=query), users=request.user)
        .values('ID', 'title')
    )
    folders = list(
        MusicSheetFolder.objects.filter(Q(name__icontains=query), users=request.user)
        .values('ID', 'name')
    )
    return JsonResponse({'sheets': sheets, 'folders': folders})

# Music Notation Management

def edit_sheet(request, sheet_title):
    sheet = get_object_or_404(MusicSheet, title=sheet_title)
    current_user = UserMusicSheet.objects.filter(user=request.user,sheet=sheet.ID).first()
    
    # if not user_permission.role :
    #     messages.error(request, "You don't have permission to edit this sheet")
    #     return redirect('home')
    
    context = {
        'sheet': sheet,
        'sheet_id': sheet.ID,
        'sheet_title': sheet_title,
        'user_role' : current_user.role,
    }
    
    return render(request, 'HelloMusicApp/sheet_editor.html', context)

@require_http_methods(["POST"])
def save_sheet(request, sheet_id):
    try:
        sheet = get_object_or_404(MusicSheet, ID=sheet_id)
        user_permission = UserMusicSheet.objects.filter(sheet=sheet, user=request.user,role__in=['owner', 'editor']).first()
        
        if not user_permission.role :
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
        
        data = json.loads(request.body)
        
        # Update sheet properties including clef
        sheet.time_signature = data.get('timeSignature')
        sheet.key_signature = data.get('keySignature')
        sheet.clef_type = data.get('clefType')  # Save the clef type
        sheet.save()
        
        # Clear existing measures and notes
        sheet.measures.all().delete()
        
        # Save new measures and notes
        for measure_data in data.get('measures', []):
            measure = Measure.objects.create(
                sheet=sheet,
                measure_number=measure_data.get('measure_number'),
                time_signature=measure_data.get('time_signature')
            )
            
            # Don't create Staff records anymore
            
            # Save notes
            for note_data in measure_data.get('notes', []):
                Note.objects.create(
                    measure=measure,
                    pitch=note_data.get('pitch'),
                    duration=note_data.get('duration'),
                    tie=note_data.get('tie', ''),
                    accidental=note_data.get('accidental', ''),
                    duration_value=note_data.get('duration_value', 1.0),
                    dynamics=note_data.get('dynamics', ''),
                    articulation=note_data.get('articulation', '')
                )
            
            # Save rests
            for rest_data in measure_data.get('rests', []):
                Rest.objects.create(
                    measure=measure,
                    duration=rest_data.get('duration')
                )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def load_sheet(request, sheet_id):
    try:
        sheet = get_object_or_404(MusicSheet, ID=sheet_id)
        user_permission = UserMusicSheet.objects.filter(sheet=sheet, user=request.user,role__in=['owner', 'editor']).first()
        
        data = {
            'timeSignature': sheet.time_signature,
            'keySignature': sheet.key_signature,
            'clefType': sheet.clef_type,
            'measures': []
        }
        
        # Get all measures for this sheet, ordered by measure number
        measures = Measure.objects.filter(sheet=sheet).order_by('measure_number')
        
        for measure in measures:
            measure_data = {
                'timeSignature': measure.time_signature,
                'notes': [],
                'rests': []
            }
            
            # Get notes for this measure
            notes = Note.objects.filter(measure=measure)
            for note in notes:
                measure_data['notes'].append({
                    'pitch': note.pitch,
                    'duration': note.duration,
                    'tie': note.tie,
                    'accidental': note.accidental,
                    'duration_value': float(note.duration_value),
                    'dynamics': note.dynamics,
                    'articulation': note.articulation
                })
            
            # Get rests for this measure
            rests = Rest.objects.filter(measure=measure)
            for rest in rests:
                measure_data['rests'].append({
                    'duration': rest.duration
                })
                
            data['measures'].append(measure_data)
            
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    
@require_http_methods(["POST"])
def save_lyrics(request, sheet_id):
    try:
        data = json.loads(request.body)
        sheet = get_object_or_404(MusicSheet, ID=sheet_id)
        
        lyrics = Lyrics.objects.create(
            music_sheet=sheet,  # Changed from 'sheet' to 'music_sheet'
            text=data['text'],
            x_position=data['x_position'],
            y_position=data['y_position'],
            measure_number=data['measure_number']
        )
        
        return JsonResponse({
            'status': 'success',
            'lyrics_id': lyrics.ID
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["GET"])
def load_lyrics(request, sheet_id):
    sheet = get_object_or_404(MusicSheet, ID=sheet_id)
    lyrics = Lyrics.objects.filter(music_sheet=sheet).values(  # Changed from 'sheet' to 'music_sheet'
        'ID', 'text', 'x_position', 'y_position', 'measure_number'
    )
    
    return JsonResponse({
        'status': 'success',
        'lyrics': list(lyrics)
    })

@require_http_methods(["PUT"])
def update_lyrics(request, sheet_id, lyrics_id):
    try:
        data = json.loads(request.body)
        lyrics = get_object_or_404(Lyrics, ID=lyrics_id, music_sheet_id=sheet_id)  # Changed from 'sheet_id' to 'music_sheet_id'
        
        lyrics.text = data['text']
        lyrics.x_position = data['x_position']
        lyrics.y_position = data['y_position']
        lyrics.measure_number = data['measure_number']
        lyrics.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["DELETE"])
def delete_lyrics(request, sheet_id, lyrics_id):
    try:
        lyrics = get_object_or_404(Lyrics, ID=lyrics_id, music_sheet_id=sheet_id)
        lyrics.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Lyrics deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)