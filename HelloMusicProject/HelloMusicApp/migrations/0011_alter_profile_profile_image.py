# Generated by Django 5.1.2 on 2024-11-28 17:28

import HelloMusicApp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HelloMusicApp', '0010_alter_profile_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to=HelloMusicApp.models.Profile.user_directory_path, validators=[HelloMusicApp.models.validate_image_format]),
        ),
    ]
