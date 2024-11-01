from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    # Simple calculation (for example, adding two numbers)
    num1 = 10
    num2 = 20
    result = num1 + num2
    
    # Pass the result to the template
    return render(request, 'home.html', {'result': result})


def helloWorld(request):
    return HttpResponse("Hello World! Hihi 123")