# Generated by Django 5.1.2 on 2024-12-08 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HelloMusicApp', '0002_staff_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='musicsheet',
            name='clef_type',
            field=models.CharField(default='treble', max_length=30),
        ),
        migrations.DeleteModel(
            name='Staff',
        ),
    ]
