import requests
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django_ratelimit.decorators import ratelimit
from django.conf import settings
import os
from django.contrib.auth.models import User
from problems.models import Problem
from submissions.models import Submission
from django.db.models import Count, Q
from users.models import UsersProfile
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
        if User.objects.filter(email=email).exists():
            return render(request, 'registration/registration.html', {
                'error': 'Email already registered'
            })
        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        UsersProfile.objects.create(user=user)
        # Optionally log the user in immediately
        login(request, user)

        return redirect("/")
    return render(request,"registration/registration.html")


def user_profile(request, username):
    try:
        user = User.objects.get(username=username)
        # total_submissions = user.submissions.count()
        # accepted_count = user.submissions.filter(status='Accepted').count()
        # percent_accepted = (accepted_count / total_submissions * 100) if total_submissions > 0 else 0.0
        total_solved = Submission.objects.filter(user=user, verdict='Accepted').values('problem_id').distinct().count()

        total_submissions = Submission.objects.filter(user=user).count()
        if total_submissions > 0:
            acceptance_rate = (Submission.objects.filter(user=user, verdict='Accepted').count() / total_submissions) * 100
        else:
            acceptance_rate = 0.0
        acceptance_rate = "{:.2f}".format(acceptance_rate)
        
        easy_solved = Submission.objects.filter(
            user=user,
            verdict='Accepted',
            problem__difficulty='Easy'
        ).values('problem_id').distinct().count()

        medium_solved = Submission.objects.filter(
            user=user,
            verdict='Accepted',
            problem__difficulty='Medium'
        ).values('problem_id').distinct().count()

        hard_solved = Submission.objects.filter(
            user=user,
            verdict='Accepted',
            problem__difficulty='Hard'
        ).values('problem_id').distinct().count()

        easy_percentage = (easy_solved / total_solved * 100) if total_solved > 0 else 0.0
        medium_percentage = (medium_solved / total_solved * 100) if total_solved > 0 else 0.0
        hard_percentage = (hard_solved / total_solved * 100) if total_solved > 0 else 0.0
        overall_percentage = (total_solved / Problem.objects.count() * 100) if Problem.objects.count() > 0 else 0.0
        
        total_problems = Problem.objects.count()
        users = (
            User.objects.annotate(
                solved_count=Count(
                    'submission__problem',
                    filter=Q(submission__verdict='Accepted'),
                    distinct=True
                )
            )
            .order_by('-solved_count','date_joined')
        )
        user_rank = users.filter(solved_count__gt=users.get(id=user.id).solved_count).count() + 1

        return render(request, 'user/userProfile.html', {
            'user':request.user,
            'user_url': user,
            'total_solved': total_solved,
            'total_submissions': total_submissions,
            'total_problems': total_problems,
            'acceptance_rate': acceptance_rate,
            'user_rank': user_rank,
            'easy_solved': easy_solved,
            'medium_solved': medium_solved,
            'hard_solved': hard_solved,
            'easy_percentage': easy_percentage,
            'medium_percentage': medium_percentage,
            'hard_percentage': hard_percentage,
            'overall_percentage': overall_percentage,
            'current_streak': 0,
            'longest_streak': 0,
            'weekly_activity': 0,
            'recent_activities': [],  # List of recent submissions
            'languages_used': [],  # Language statistics
        })
    except User.DoesNotExist:
        return render(request, 'users/profile.html', {
            'error': 'User does not exist.'
        })