import requests
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django_ratelimit.decorators import ratelimit
from django.conf import settings
import os
# from captcha.fields import ReCaptchaField


# Create your views here.
BADWORDS_FILE_PATH = os.path.join(os.path.dirname(__file__), "badwords.txt")

with open(BADWORDS_FILE_PATH, encoding="utf-8") as f:
    bad_words = set(line.strip().lower() for line in f if line.strip())

def contains_profanity(value):
    value = value.lower()
    for word in bad_words:
        if word in value:
            return True
    return False


@ratelimit(key='ip', rate='5/m', block=True)
def register_views(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        captcha_response = request.POST.get('g-recaptcha-response')
        # Check CAPTCHA
        email = email.lower()
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
        email_local_part = email.split("@")[0] if "@" in email else email
        # Check bad words
        if contains_profanity(username) or contains_profanity(email_local_part):
            return render(request, 'registration/registration.html', {
                'error': 'Username or email contains prohibited words.'
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

