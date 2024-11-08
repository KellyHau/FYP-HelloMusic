# Generated by Django 5.1.3 on 2024-11-08 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HelloMusicApp', '0002_alter_musicsheet_folderid_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chord',
            old_name='measureID',
            new_name='measure',
        ),
        migrations.RenameField(
            model_name='lyrics',
            old_name='noteID',
            new_name='note',
        ),
        migrations.RenameField(
            model_name='measure',
            old_name='sheetID',
            new_name='sheet',
        ),
        migrations.RenameField(
            model_name='musicsheet',
            old_name='folderID',
            new_name='folder',
        ),
        migrations.RenameField(
            model_name='musicsheetfolder',
            old_name='ownerID',
            new_name='owner',
        ),
        migrations.RenameField(
            model_name='note',
            old_name='measureID',
            new_name='measure',
        ),
        migrations.RenameField(
            model_name='rest',
            old_name='measureID',
            new_name='measure',
        ),
        migrations.RenameField(
            model_name='staff',
            old_name='sheetID',
            new_name='sheet',
        ),
        migrations.RenameField(
            model_name='usermusicsheet',
            old_name='sheetID',
            new_name='sheet',
        ),
        migrations.RenameField(
            model_name='usermusicsheet',
            old_name='userID',
            new_name='user',
        ),
    ]
