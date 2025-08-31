from django.shortcuts import render

# Create your views here.
def home(request):
    title = 'Master Your <span class="bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent inline-block">Coding Skills</span>'
    return render(request, "home/index.html", {"title": title})
