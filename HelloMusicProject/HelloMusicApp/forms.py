from django import forms
from .models import *
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class MusicSheetForm(forms.ModelForm):
    class Meta:
        model = MusicSheet
        fields = ['title']
        
class MusicSheetFolderForm(forms.ModelForm):
    class Meta:
        model = MusicSheetFolder
        fields = ['name']

class AddSheetsToFolderForm(forms.Form):
    selected_sheets = forms.ModelMultipleChoiceField(
        queryset=MusicSheet.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'id': 'sheetSelection',
        }),
        label="Select Sheets",
        help_text="Hold <kbd>Ctrl</kbd> (or <kbd>Cmd</kbd> on Mac) to select multiple sheets.",
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:  # Filter queryset by user
            self.fields['selected_sheets'].queryset = MusicSheet.objects.filter(users=user)


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')  # Update this to use an underscore

        if password != confirm_password:
            raise ValidationError("Passwords do not match")
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email already exists. Please use other email to register.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password before saving
        if commit:
            user.save()
        return user        

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    profile_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        try:
            self.fields['profile_image'].initial = self.user.profile.profile_image
        except Profile.DoesNotExist:
            print("this path got error at forms.py")
            pass
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("This email is already in use by another account.")
        return email
        
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            # Update profile image if provided
            if self.cleaned_data.get('profile_image'):
                profile.profile_image = self.cleaned_data['profile_image']
                profile.save()
        return user