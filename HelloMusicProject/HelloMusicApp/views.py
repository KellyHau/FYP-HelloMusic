import json
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login as auth_login 
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
import os
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Q
from music21 import chord

C_MAJOR_KEY_LIB= {
    "C"  :{ "name": "C Major", "notes": ["C4", "E4", "G4"], "type": "triad" },
    "Dm" :{ "name": "D Minor", "notes": ["D4", "F4", "A4"], "type": "triad" },
    "Em" :{ "name": "E Minor", "notes": ["E4", "G4", "B4"], "type": "triad" },
    "F"  :{ "name": "F Major", "notes": ["F4", "A4", "C5"], "type": "triad" },
    "G"  :{ "name": "G Major", "notes": ["G4", "B4", "D5"], "type": "triad" },
    "Am" :{  "name": "A Minor", "notes": ["A3", "C4", "E4"], "type": "triad" },
    "Bdim" :{ "name": "B Diminished", "notes": ["B3", "D4", "F4"], "type": "triad" },
}


# User Management --------------------------------------------------------------------------------
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

# Music sheet management -----------------------------------------------------------------------------------------------------------------------
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


def edit_sheet(request, sheet_title):
    sheet = get_object_or_404(MusicSheet, title=sheet_title)
    current_user = UserMusicSheet.objects.filter(user=request.user,sheet=sheet.ID).first()
    chord_library = user_chord_library(request)
    
    context = {
        'sheet': sheet,
        'sheet_id': sheet.ID,
        'sheet_title': sheet_title,
        'user_role' : current_user.role,
        'chord_library' : chord_library,
    }
    
    return render(request, 'HelloMusicApp/sheet_editor.html', context)


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
        
        if not email:
            return JsonResponse({'status': False, 'mes': 'Email field cannot be empty'})
     
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'status': False, 'mes': 'Invalid email format'})
        
        try:
            user = User.objects.get(email=email)
            sheet = MusicSheet.objects.get(ID=sheet_id)
         
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
        except Exception as e:
            return JsonResponse({'status': False, 'mes': f'{str(e)}'})
   
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
                "email": user.user.email,
                "role": user.role
            }
            for user in users
        ]
         
        data = { 
                "users": user_list,
                "current_role": current_user.role ,
            }
        return JsonResponse(data)

# Remove user sheet permission
@require_POST
def remove_sheet_permission(request, sheet_id):

    email = request.POST.get('email', '').strip()
    try:
        # Get the UserMusicSheet entry for the given email and sheet ID
        user_music_sheet = get_object_or_404(UserMusicSheet, sheet=sheet_id, user__email=email)

        # Delete the entry
        user_music_sheet.delete()

        return JsonResponse({'status': True, 'mes': f'Permission removed for {email}'})
    except UserMusicSheet.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Permission not found for the given user and sheet'})
    except Exception as e:
        return JsonResponse({'status': False, 'mes': f'An error occurred: {str(e)}'})
  
    
# Filter sheet
def filter_music_sheets(request):
    key_signature = request.GET.get('key_signature', '')
    clef = request.GET.get('clef', '')
    time_signature = request.GET.get('time_signature', '')

    music_sheets = MusicSheet.objects.all()

    if key_signature:
        music_sheets = music_sheets.filter(key_signature=key_signature)
    if clef:
        music_sheets = music_sheets.filter(clef_type=clef)
    if time_signature:
        music_sheets = music_sheets.filter(time_signature=time_signature)

    # Render partial HTML for the music sheet list
    return render(request, 'HelloMusicApp/partials/music_sheet_filter.html', {'music_sheets': music_sheets})


# Music sheet folder management -----------------------------------------------------------------------------------------------------
@require_POST
def create_folder(request): #need to login before create
    
    form = MusicSheetFolderForm(request.POST,user=request.user)
    
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
                "email": user.user.email,
                "role": user.role
            }
            for user in users
        ]
         
        data = { 
                "users": user_list,
                "current_role": current_user.role ,
            }
        return JsonResponse(data)
        

# Remove user folder permission
@require_POST
def remove_folder_permission(request, folder_id):

    email = request.POST.get('email', '').strip()
    try:
        # Get the UserMusicSheet entry for the given email and sheet ID
        user_folder = get_object_or_404(UserMusicSheetFolder, folder=folder_id, user__email=email)

        # Delete the entry
        user_folder.delete()

        return JsonResponse({'status': True, 'mes': f'Permission removed for {email}'})
    except UserMusicSheet.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Permission not found for the given user and folder'})
    except Exception as e:
        return JsonResponse({'status': False, 'mes': f'An error occurred: {str(e)}'})
    

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

# Chord Management ------------------------------------------------------------------------------------------------------------------------------
@require_POST
def create_library(request):
    name = request.POST.get('name', '').strip() 

    # Validation: Ensure the name is not empty
    if not name:
        return JsonResponse({
            'status': False,
            'mes': 'Library name cannot be empty.'
        })

    existing_library = ChordLibrary.objects.filter(name=name).first()
    

    if existing_library:
        counter = 1
        new_name = f"{name} {counter}"
      
        while ChordLibrary.objects.filter(name=new_name).exists():
            counter += 1
            new_name = f"{name} {counter}"
        name = new_name

 
    ChordLibrary.objects.create(
        name=name,
        user=request.user,  # Assuming you're associating the library with the logged-in user
    )

    return JsonResponse({
        'status': True,
        'mes': 'Chord library created successfully!'
    })


def user_chord_library(request):
    return ChordLibrary.objects.filter(user=request.user)

@require_POST
def rename_library(request, library_id):
    
    new_name = request.POST.get('name', '').strip()    
    
    # Validation: Ensure the name is not empty
    if not new_name:
        return JsonResponse({
            'status': False,
            'mes': 'Library name cannot be empty.'
        })
    
    library = get_object_or_404(ChordLibrary, ID=library_id)    
    
    library.name = new_name
    library.save()

    return JsonResponse({'status': True, 'mes': 'Library rename successfully.'})


@require_POST
def delete_library(request, library_id): 

    try:    
    
        library = get_object_or_404(ChordLibrary, ID=library_id)    
        
        library.delete()
        
        return JsonResponse({'status': True, 'mes': 'Library deleted successfully.'})
    
    except MusicSheetFolder.DoesNotExist:
        return JsonResponse({'status': False, 'mes': 'Library not found'})
    


def create_chord(request,library_data):
 
    for chord_data in library_data:
        symbol = chord_data['symbol']
        notes = ",".join(chord_data['notes'])  
              
        chord, created = Chord.objects.get_or_create(
        chord_symbol=symbol,
        defaults={'note': notes}
        )
    

def update_library(request,library_id):

    if request.method == "POST":
        try:
            chord_library = get_object_or_404(ChordLibrary, ID=library_id)
           
            data = json.loads(request.body)
            library_data = data.get('libraryData', [])         
            
            create_chord(request,library_data)

            chord_library.chords.clear()
            for data in library_data:
                chord = get_object_or_404(Chord, chord_symbol=data['symbol'])
                chord_library.chords.add(chord)

            chord_library.save()

            return JsonResponse({'status': True, 'mes': 'Chord library saved successfully!'})
        except Exception as e:
            return JsonResponse({'status': False, 'mes': str(e)}, status=400)
    
    if request.method == "GET":
        chord_library = get_object_or_404(ChordLibrary, ID=library_id)

        # Get the chords in the library
        chords = chord_library.chords.all()

        # Prepare the chords for the template
        data = [
            {
                'symbol': chord.chord_symbol,
            }
            for chord in chords
        ]

        return JsonResponse(data, safe = False)

    
def generate_chord(chord_symbol):
   # Retrieve chord data from the C_MAJOR_KEY_LIB
    if chord_symbol in C_MAJOR_KEY_LIB:
        chord_data = C_MAJOR_KEY_LIB[chord_symbol]
        music21_chord = chord.Chord(chord_data["notes"])
        music21_chord.duration.quarterLength = 4  # Duration of a whole note
        
        # Construct the output dictionary
        output = {
            "symbol": chord_symbol,
            "name" : chord_data["name"],
            "notes": [n.nameWithOctave for n in music21_chord.pitches],
            "duration": music21_chord.duration.quarterLength,
            "type": chord_data["type"]
        }
        return output
    else:
        raise ValueError(f"Chord '{chord_symbol}' not found in the library")
    

# Generate and export multiple chords
exported_chords = []
for chord_symbol in C_MAJOR_KEY_LIB.keys():
    exported_chords.append(generate_chord(chord_symbol))

output_path = os.path.join(settings.BASE_DIR, "HelloMusicApp" ,"static", "HelloMusicApp", "chords.json")

# Ensure the static directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

 # Export chord as JSON
import json
with open(output_path, "w") as file:
    json.dump(exported_chords, file, indent=4)


# Music Notation Management -----------------------------------------------------------------------------------------------------
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

