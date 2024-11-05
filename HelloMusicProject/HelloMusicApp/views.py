from django.shortcuts import render

def home(request):
    context={}
    return render(request,"HelloMusicApp/index.html",context)


def folder(request):
    context={}
    return render(request,"HelloMusicApp/folder.html",context)

