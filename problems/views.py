from django.shortcuts import render, get_object_or_404, redirect
from .models import ContestSubmission, Problem, Tag, ContestRegistration, Contest, ProblemSolution
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from submissions.models import Submission
from django.db.models import Subquery
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


def problem_list(request):
    tag_name = request.GET.get('tag')
    difficulty = request.GET.get('difficulty')

    problems = Problem.objects.all().order_by('id')

    # filter by tag
    if tag_name:
        problems = problems.filter(tags__name=tag_name)

    # filter by difficulty
    if difficulty:
        problems = problems.filter(difficulty=difficulty)

    tags = Tag.objects.all()

    # Pagination (3 problems per page for testing; you can change it to 10/20 later)
    paginator = Paginator(problems, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    problem_total_count = problems.count()
    if request.user.is_authenticated:
        # Count the number of problems solved by the user
        solved_count = Submission.objects.filter(user=request.user, verdict='Accepted').values('problem_id').distinct().count()
    else:
        solved_count = 0
    progress = int((solved_count / problem_total_count) * 100) if problem_total_count > 0 else 0
    if request.user.is_authenticated:
        problem_isSolved = set(Submission.objects.filter(user=request.user, verdict='Accepted').values_list("problem_id", flat=True))
    else:
        problem_isSolved = set()

    return render(request, 'problems/problem_list.html', {
        'problems': page_obj,   # renamed to page_obj (Django convention)
        'tags': tags,
        'selected_tag': tag_name,
        'selected_difficulty': difficulty,
        'solved_count' :solved_count,
        'problem_total_count': problem_total_count,
        'progress': progress,
        'problem_isSolved' :problem_isSolved,
    })


# @login_required
def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    default_language = 'python'

    last_submission = None

    if request.user.is_authenticated:
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

        # Fetch all submissions for this problem
        submission_history = (
            Submission.objects.filter(
                user=request.user,
                problem=problem
            ).order_by('-created_at')
        )
    else:
        language = default_language
        submission_history = Submission.objects.none()

    paginator = Paginator(submission_history, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    problem_solutions = ProblemSolution.objects.filter(problem=problem).first()
    
    if problem_solutions:
        problem_code = problem_solutions.code
    else:
        problem_code = "No solutions available."
    # print(problem_code)
        # problem_code = "No solutions available."
    
    return render(request, 'problems/problem_detail.html', {
        'problem': problem,
        'last_submission': last_submission,
        'selected_language': language,
        'submission_history': page_obj,
        'problem_code':problem_code,
    })

def contest_list(request):
    now = timezone.now()
    contests = Contest.objects.all().order_by('-start_time')

    # Attach duration in hours directly to each contest
    for contest in contests:
        duration = contest.end_time - contest.start_time
        contest.duration_hours = int(round(duration.total_seconds() // 3600, 2))  # in hours

    context = { 
        'contests': contests,
        'now': now,
    }
    return render(request, 'problems/contest_list.html', context)

@login_required
def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    problems = contest.problems.all()
    now = timezone.now()

    # Create a dictionary: problem_id -> verdict
    submission_status = {}
    for problem in problems:
        latest_submission = (
            ContestSubmission.objects
            .filter(user=request.user, contest=contest, problem=problem)
            .order_by('-created_at')
            .first()
        )
        if latest_submission:
            submission_status[problem.id] = latest_submission.verdict
        else:
            submission_status[problem.id] = "Unattempted"   
    duration = contest.end_time - contest.start_time
    contest.duration_hours = int(round(duration.total_seconds() // 3600, 2))  # in hours
    context = {
        'contest': contest,
        'problems': problems,
        'now': now,
        'submission_status': submission_status,
    }
    
    return render(request, 'problems/contest_detail.html',context )


def contest_leaderboard(request, pk):
    contest = get_object_or_404(Contest, pk=pk)

    registered_users = ContestRegistration.objects.filter(contest=contest).values('user_id')

    users = (
        User.objects
        .filter(id__in=Subquery(registered_users))
        .annotate(
            solved_count=Count(
                'contestsubmission__problem',
                filter=Q(contestsubmission__contest=contest, contestsubmission__verdict='Accepted'),
                distinct=True
            )
        )
        .order_by('-solved_count', 'username')
    )
    return render(request, 'problems/contest_leaderboard.html', {'contest': contest, 'users': users})

def logout_view(request):
    logout(request)
    return redirect("/")


@login_required
def register_for_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    ContestRegistration.objects.get_or_create(user=request.user, contest=contest)
    return redirect('contest_detail', pk=contest.pk)



@login_required
def contest_problem_detail(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    problem = get_object_or_404(Problem, pk=problem_id)

    # Check if contest is running
    now = timezone.now()
    if now < contest.start_time:
        return redirect('contest_detail', pk=contest.id)
    if now > contest.end_time:
        return redirect('contest_detail', pk=contest.id)

    # Check if user is registered
    if not ContestRegistration.objects.filter(user=request.user, contest=contest).exists():
        return redirect('contest_detail', pk=contest.id)

    # Default language
    default_language = 'python'

    # Allow switching language via query param
    language = request.GET.get('language', default_language)

    # Fetch last submission
    last_submission = (
        ContestSubmission.objects
        .filter(
            user=request.user,
            contest=contest,
            problem=problem,
            language=language
        )
        .order_by('-created_at')
        .first()
    )

    return render(request, 'problems/contest_problem_detail.html', {
        'contest': contest,
        'problem': problem,
        'last_submission': last_submission,
        'selected_language': language,
        'end_time': contest.end_time.isoformat(),
    })
