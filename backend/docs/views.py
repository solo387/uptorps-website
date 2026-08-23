from django.shortcuts import render

# Create your views here.
def auth_docs(request):
    return render(request,'docs/account/index.html',{})

def quiz_docs(request):
    return render(request,'docs/quiz/index.html',{})