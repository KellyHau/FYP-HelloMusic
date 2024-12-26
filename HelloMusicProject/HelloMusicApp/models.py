from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import localtime
from django.core.exceptions import ValidationError
import os

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    new_password = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
def validate_image_format(value):
    ext = os.path.splitext(value.name)[1]  # Get the file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file format. Please use JPG, JPEG, PNG, or GIF.')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def user_directory_path(instance, filename):
        # File will be uploaded to MEDIA_ROOT/user_<id>.<extension>
        extension = filename.split('.')[-1]
        return f'user_{instance.user.id}.{extension}'

    profile_image = models.ImageField(
        upload_to=user_directory_path,
        validators=[validate_image_format],
        null=True,
        blank=True,
        default='default_profile.png'
    )
    
    def save(self, *args, **kwargs):
        if self.pk:  # If this is an update
            old_instance = Profile.objects.get(pk=self.pk)
            if old_instance.profile_image and self.profile_image != old_instance.profile_image:
                if old_instance.profile_image.name != 'default_profile.png':
                    old_instance.profile_image.delete(save=False)
        super().save(*args, **kwargs)
    
class MusicSheetFolder(models.Model):
    
    ID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    creationDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, through="UserMusicSheetFolder", related_name="user_sheet_folders")

    def __str__(self):
        return self.name
    
    def update_time(self):
        self.updatedDate = localtime()
        self.save()


class MusicSheet(models.Model):
    
    ID = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    tempo = models.CharField(max_length=30, null=True, blank=True)
    key_signature = models.CharField(max_length=30, null=True, blank=True)
    time_signature = models.CharField(max_length=30, null=True, blank=True)
    clef_type = models.CharField(max_length=30, default='treble') 
    folder =  models.ForeignKey(MusicSheetFolder, on_delete=models.CASCADE,related_name="music_sheets", null=True, blank=True)
    creationDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, through="UserMusicSheet", related_name="user_music_sheets")

    def __str__(self):
        return self.title
    
class UserMusicSheet(models.Model):
    
    sheet = models.ForeignKey(MusicSheet, on_delete=models.CASCADE)
    user =  models.ForeignKey(User, on_delete=models.CASCADE)
    last_accessed = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('viewer', 'Viewer'),
            ('editor', 'Editor'),
        ],
        default='viewer',
    )

    class Meta:
        unique_together = ('sheet', 'user')
        
    def __str__(self):
        return f"{self.user.username} in {self.sheet.title} as {self.role}"
    
    def update_access_time(self):
        self.last_accessed = localtime()
        self.save()
    
    
class UserMusicSheetFolder(models.Model):
    folder = models.ForeignKey(MusicSheetFolder, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_accessed = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('viewer', 'Viewer'),
            ('editor', 'Editor'),
        ],
        default='viewer',
    )

    class Meta:
        unique_together = ('folder', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.folder.name} as {self.role}"
    
    def update_access_time(self):
        self.last_accessed = localtime()
        self.save()
    
    
class Measure(models.Model):
    
    ID = models.AutoField(primary_key=True)
    sheet = models.ForeignKey(MusicSheet, on_delete=models.CASCADE,related_name="measures")
    measure_number = models.IntegerField()
    time_signature = models.CharField(max_length=10)

    def __str__(self):
        return self.measure_number

class Chord(models.Model):
    
    ID = models.AutoField(primary_key=True)
    chord_symbol = models.CharField(max_length=20, blank=True)
    note = models.CharField(max_length=100)
    
    def __str__(self):
        return self.chord_symbol
    
    
class ChordLibrary(models.Model):
    
    ID = models.AutoField(primary_key=True)
    name =  models.CharField(max_length=100)
    chords = models.ManyToManyField(Chord, related_name="chords",blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name 


class Rest(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="rests")
    duration = models.CharField(max_length=30)

    def __str__(self):
        return self.duration

class Note(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="notes")
    pitch = models.CharField(max_length=30)
    duration = models.CharField(max_length=30)
    tie = models.CharField(max_length=30)
    accidental = models.CharField(max_length=30)
    duration_value = models.DecimalField(max_digits=7, decimal_places=5)    
    dynamics = models.CharField(max_length=30)
    articulation = models.CharField(max_length=30)

    def __str__(self):
        return self.pitch
    
class Lyrics(models.Model):
    ID = models.AutoField(primary_key=True)
    music_sheet = models.ForeignKey(MusicSheet, on_delete=models.CASCADE, related_name="lyrics")  # Changed from 'sheet' to 'music_sheet'
    text = models.CharField(max_length=255)
    x_position = models.FloatField()
    y_position = models.FloatField()
    measure_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['y_position', 'x_position']
        
    def __str__(self):
        return f"Lyrics '{self.text}' at measure {self.measure_number}"