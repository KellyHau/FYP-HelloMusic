# Generated by Django 5.1.2 on 2024-12-08 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HelloMusicApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='position',
            field=models.IntegerField(default=0),
        ),
    ]