from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
# Create your views here.
def register_views(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Basic validation
        if password != confirm_password:
            # You can add a message or return an error page here
            return render(request, 'registration/registration.html', {
                'error': 'Passwords do not match'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'registration/registration.html', {
                'error': 'Username already taken'
            })

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)

        # Optionally log the user in immediately
        login(request, user)

        return redirect("/")
    return render(request,"registration/registration.html")

