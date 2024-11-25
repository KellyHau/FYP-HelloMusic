from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import localtime


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

class Staff(models.Model):
    
    ID = models.AutoField(primary_key=True)
    sheet = models.ForeignKey(MusicSheet, on_delete=models.CASCADE,related_name="staffs")
    instrument = models.CharField(max_length=50)
    clef_type = models.CharField(max_length=50)

    def __str__(self):
        return self.instrument

class Chord(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="chords")
    note = models.CharField(max_length=100)
    chord_symbol = models.CharField(max_length=30)

    def __str__(self):
        return self.chord_symbol

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
    note = models.ForeignKey(Note, on_delete=models.CASCADE,related_name="lyrics")
    text = models.CharField(max_length=30)
    syllable_type = models.CharField(max_length=30)

    def __str__(self):
        return self.text