from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem, Tag
from .models import Contest
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from submissions.models import Submission

def problem_list(request):
    tag_name = request.GET.get('tag')
    difficulty = request.GET.get('difficulty')

    problems = Problem.objects.all()

    if tag_name:
        problems = problems.filter(tags__name=tag_name)

    if difficulty:
        problems = problems.filter(difficulty=difficulty)

    tags = Tag.objects.all()

    return render(request, 'problems/problem_list.html', {
        'problems': problems,
        'tags': tags,
        'selected_tag': tag_name,
        'selected_difficulty': difficulty,
    })


def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    default_language = 'python'

    last_submission = None

    if request.user.is_authenticated:
        # Check if language is passed as query param (?language=cpp)
        language = request.GET.get('language', default_language)
        last_submission = (
            Submission.objects.filter(
                user=request.user,
                problem=problem,
                language=language
            )
            .order_by('-created_at')
            .first()
        )
    else:
        language = default_language

    return render(request, 'problems/problem_detail.html', {
        'problem': problem,
        'last_submission': last_submission,
        'selected_language': language
    })


def contest_list(request):
    now = timezone.now()
    contests = Contest.objects.all().order_by('-start_time')
    return render(request, 'problems/contest_list.html', {'contests': contests, 'now': now})

def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    problems = contest.problems.all()
    now = timezone.now()
    return render(request, 'problems/contest_detail.html', {
        'contest': contest,
        'problems': problems,
        'now': now
    })

def contest_leaderboard(request, pk):
    contest = get_object_or_404(Contest, pk=pk)

    users = (
        User.objects.annotate(
            solved_count=Count(
                'contestsubmission__problem',
                filter=Q(contestsubmission__contest=contest, contestsubmission__verdict='Accepted'),
                distinct=True
            )
        )
        .order_by('-solved_count', 'username')
    )

    return render(request, 'problems/contest_leaderboard.html', {
        'contest': contest,
        'users': users,
    })

def logout_view(request):
    logout(request)
    return redirect("/")