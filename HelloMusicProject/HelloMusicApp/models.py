from django.db import models
from django.contrib.auth.models import User


class MusicSheetFolder(models.Model):
    
    ID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    ownerID = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    creationDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MusicSheet(models.Model):
    
    ID = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    tempo = models.CharField(max_length=30)
    key_signature = models.CharField(max_length=30)
    time_signature = models.CharField(max_length=30)
    folderID =  models.ForeignKey(MusicSheetFolder, on_delete=models.CASCADE,related_name="music_sheets")
    creationDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, through="UserMusicSheet", related_name="music_sheets")

    def __str__(self):
        return self.title
    
class UserMusicSheet(models.Model):
    
    sheetID = models.ForeignKey(MusicSheet, on_delete=models.CASCADE)
    userID =  models.ForeignKey(User, on_delete=models.CASCADE)
    
    
class Measure(models.Model):
    
    ID = models.AutoField(primary_key=True)
    sheetID = models.ForeignKey(MusicSheet, on_delete=models.CASCADE,related_name="measures")
    measure_number = models.IntegerField()
    time_signature = models.CharField(max_length=10)

    def __str__(self):
        return self.measure_number

class Staff(models.Model):
    
    ID = models.AutoField(primary_key=True)
    sheetID = models.ForeignKey(MusicSheet, on_delete=models.CASCADE,related_name="staffs")
    instrument = models.CharField(max_length=50)
    clef_type = models.CharField(max_length=50)

    def __str__(self):
        return self.instrument

class Chord(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measureID = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="chords")
    note = models.CharField(max_length=100)
    chord_symbol = models.CharField(max_length=30)

    def __str__(self):
        return self.chord_symbol

class Rest(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measureID = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="rests")
    duration = models.CharField(max_length=30)

    def __str__(self):
        return self.duration

class Note(models.Model):
    
    ID = models.AutoField(primary_key=True)
    measureID = models.ForeignKey(Measure, on_delete=models.CASCADE,related_name="notes")
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
    noteID = models.ForeignKey(Note, on_delete=models.CASCADE,related_name="lyrics")
    text = models.CharField(max_length=30)
    syllable_type = models.CharField(max_length=30)

    def __str__(self):
        return self.text