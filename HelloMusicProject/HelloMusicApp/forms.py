from django import forms
from .models import *
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class MusicSheetForm(forms.ModelForm):
    class Meta:
        model = MusicSheet
        fields = ['title']

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