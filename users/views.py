import requests
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django_ratelimit.decorators import ratelimit
from django.conf import settings
# from captcha.fields import ReCaptchaField


# Create your views here.
wrong_content = set("")

@ratelimit(key='ip', rate='5/m', block=True)
def register_views(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        captcha_response = request.POST.get('g-recaptcha-response')
        # Check CAPTCHA
        data = {
            'secret': '6LdsI3orAAAAAEMrToOKWfw6cvzvpWOr03oqtgMM',  # replace with your secret
            'response': captcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        
        if not result.get('success'):
            return render(request, 'registration/registration.html', {
                'error': 'Invalid CAPTCHA. Please try again.'
            })
        
        if len(username)>15 or len(username)<=4:
            # You can add a message or return an error page here
            return render(request, 'registration/registration.html', {
                'error': "Make username under 4 - 15 letters"
            })
        
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

