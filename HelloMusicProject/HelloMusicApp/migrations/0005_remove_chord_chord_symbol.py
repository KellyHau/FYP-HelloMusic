# Generated by Django 5.1.3 on 2024-12-11 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HelloMusicApp', '0004_lyrics'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chord',
            name='chord_symbol',
        ),
    ]
