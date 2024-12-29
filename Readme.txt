-----------------------------------------------------------------------
				
				Hello Music

-----------------------------------------------------------------------

## Overview
This is a free music sheet editor web application suitable for music beginner to get start the music leaning process. 
User can register, login, create and update music sheet and music folder, share the music sheet with other user. 

##Steps
# Installation
1. Hello Music Project
https://github.com/KellyHau/FYP-HelloMusic.git
Download the project zip file from the link and ensure the project folder name as "FYP-HelloMusic".


2. Python
https://www.python.org/downloads/
Install Python based on your OS form the website. 


3. Virtual Environment
	1. Open visual studio and open the "FYP-HelloMusic" folder
	2. Open terminal, choose CMD or PowerShell
	3. Under the root folder "/FYP-HelloMusic", run this command:
		python -m venv Venv (Cmd)
		py -m venv Venv (PowerShell)

Ensure the current location is in the root folder "/FYP-HelloMusic", activate the virtual environment:
		cd FYP-HelloMusic
		./Venv/Scripts/activate


4. Library
Activate the virtual environment and run the following command: 
**Before type the command please ensure the root like this "(Venv) PS C:\FYP-HelloMusic>" 
		pip install -r requirements.txt


5. Database
https://dev.mysql.com/downloads/installer/ 
Go to the above website, select Windows (x86, 32bit) 8.0.40 version to install.

https://www.youtube.com/watch?v=UgHRay7gN1g
The above Youtube link is the detail guide to install MySQL.

After successful install MySQL, open the cmd terminal on your computer to create the database:
	MySQL -u root -p
	Enter password: abc123 (or your own created password, this password must same with the password in settings.py under DATABASES section)
	CREATE DATABASE hellomusic; 

** If you using the password different to above password, please go to "/HelloMusicProject/HelloMusicProject" directory and click on "settings.py"
** Finf and modify below section

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hellomusic',
        'USER': 'root',
        'PASSWORD': 'abc123', --> password follow your createds password
        'HOST': '127.0.0.1',  
        'PORT': '3306',       
    }
}

6. Updating Hello Music table into database
Run this command after database successfully setup:
**Before type the command please ensure the root like this "(Venv) PS C:\FYP-HelloMusic>" 

	(Cmd)
	python manage.py makemigrations
	python manage.py migrates

	(PowerShell)
	py manage.py makemigrations
	py manage.py migrates

To verify whether the database has been create successful or not, enter the following command: 
** root : "C:\FYP-HelloMusic>" 
** NOT IN Virtual Environment

	MySQL -u root -p
	Enter password: password(Your create before)
	use hellomusic;
	show tables;
Now you should able to see the tables use by Hello Music listed (should have 23 tables shown).


## Usage
The user must have web browser to open this project, such as Google Chrome and Microsoft Edge. 

This project is developed using Django and MySQL database, thus user need to run the following command to redirect to Hello Music website in the bash terminal: 

1. Ensure the virtual environment has been activated:
	cd FYP-HelloMusic
	./Venv/Scripts/activate

2. Ensure current location is "\FYP-HelloMusic\HelloMusicProject" : 
	cd HelloMusicProject

3. Run this command to get the project working: 
	python manage.py runserver (Cmd)
	py manage.py runserver (PowerShell)

4. Now should get meesage to go http://127.0.0.1:8000/ 
5. Click on the http link and the webpage will now open in your default browser. 
**CTRL + C on terminal to quit the server.



Happy Testing!
