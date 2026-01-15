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
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from users.models import UserProfile
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
        # Optionally log the user in immediately
        login(request, user)

        return redirect("/")
    return render(request,"registration/registration.html")


def user_profile(request, username):
    try:
        user_url = User.objects.get(username=username)
        user = request.user
        if user_url==user:
            is_own_profile = True
        else:
            is_own_profile = False
        print(user)
        # total_submissions = user.submissions.count()
        # accepted_count = user.submissions.filter(status='Accepted').count()
        # percent_accepted = (accepted_count / total_submissions * 100) if total_submissions > 0 else 0.0
        total_solved = Submission.objects.filter(user=user_url, verdict='Accepted').values('problem_id').distinct().count()
        user_profile = UserProfile.objects.get(user=user_url)
        total_submissions = Submission.objects.filter(user=user_url).count()
        if total_submissions > 0:
            acceptance_rate = (Submission.objects.filter(user=user_url, verdict='Accepted').count() / total_submissions) * 100
        else:
            acceptance_rate = 0.0
        acceptance_rate = "{:.2f}".format(acceptance_rate)
        
        easy_solved = Submission.objects.filter(
            user=user_url,
            verdict='Accepted',
            problem__difficulty='Easy'
        ).values('problem_id').distinct().count()

        medium_solved = Submission.objects.filter(
            user=user_url,
            verdict='Accepted',
            problem__difficulty='Medium'
        ).values('problem_id').distinct().count()

        hard_solved = Submission.objects.filter(
            user=user_url,
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
        user_rank = users.filter(solved_count__gt=users.get(id=user_url.id).solved_count).count() + 1

        return render(request, 'user/userProfile.html', {
            'is_own_profile':is_own_profile,
            'user_profile': user_profile,
            'user_url': user_url,
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

# views.py

@login_required
@require_http_methods(["GET"])
def profile_edit_form(request):
    """Returns the edit profile form modal"""
    try:
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'location': 'Unknown',
                'bio': '',
                'rank': 'Beginner'
            }
        )
        
        # Prepare context data
        context = {
            'user_profile': user_profile,
            'username': request.user.username,
            'email': request.user.email,
        }
        
        return render(request, 'user/profile_edit_form.html', context)
        
    except Exception as e:
        # Return error modal if something goes wrong
        return render(request, 'user/profile_edit_error.html', {
            'error_message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def profile_edit_save(request):
    """Saves the profile edits and returns success message"""
    try:
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'location': 'Unknown',
                'bio': '',
                'rank': 'Beginner'
            }
        )
        
        # Update fields from POST data
        location = request.POST.get('location', '').strip()
        bio = request.POST.get('bio', '').strip()
        
        # Validate data
        if len(location) > 100:
            raise ValueError("Location must be less than 100 characters")
        
        if len(bio) > 500:
            raise ValueError("Bio must be less than 500 characters")
        
        # Update profile
        user_profile.location = location if location else 'Unknown'
        user_profile.bio = bio
        user_profile.save()
        
        # Return success modal
        return HttpResponse("""
            <div class="modal-overlay">
                <div class="modal">
                    <div class="modal-header">
                        <h2 class="modal-title">Success!</h2>
                        <button class="modal-close" onclick="window.location.reload()">✕</button>
                    </div>
                    <div style="padding: 20px; text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 16px; color: #3fb950;">✓</div>
                        <p style="font-size: 16px; color: #c9d1d9; margin-bottom: 24px;">Profile updated successfully!</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            Refresh Page
                        </button>
                    </div>
                </div>
            </div>
        """)
        
    except ValueError as e:
        # Validation error
        return HttpResponse(f"""
            <div class="modal-overlay">
                <div class="modal">
                    <div class="modal-header">
                        <h2 class="modal-title">Validation Error</h2>
                        <button class="modal-close" onclick="document.getElementById('modal-container').innerHTML = ''">✕</button>
                    </div>
                    <div style="padding: 20px; text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 16px; color: #d29922;">⚠</div>
                        <p style="font-size: 16px; color: #c9d1d9; margin-bottom: 24px;">{str(e)}</p>
                        <button class="btn btn-secondary" onclick="document.getElementById('modal-container').innerHTML = ''">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        """, status=400)
        
    except Exception as e:
        # General error
        return HttpResponse(f"""
            <div class="modal-overlay">
                <div class="modal">
                    <div class="modal-header">
                        <h2 class="modal-title">Error</h2>
                        <button class="modal-close" onclick="document.getElementById('modal-container').innerHTML = ''">✕</button>
                    </div>
                    <div style="padding: 20px; text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 16px; color: #f85149;">✗</div>
                        <p style="font-size: 16px; color: #c9d1d9; margin-bottom: 24px;">Failed to update profile. Please try again.</p>
                        <button class="btn btn-secondary" onclick="document.getElementById('modal-container').innerHTML = ''">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        """, status=500)