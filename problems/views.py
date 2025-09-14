from django.shortcuts import render, get_object_or_404, redirect
from .models import ContestSubmission, Problem, Tag, ContestRegistration, Contest, ProblemSolution, ProblemVariant
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from submissions.models import Submission
from django.db.models import Subquery
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import random, string
from django.contrib import messages
import json
from django.conf import settings
import requests

def problem_list(request):
    tag_name = request.GET.get('tag')
    difficulty = request.GET.get('difficulty')

    problems = Problem.objects.all().order_by('id')
    ai_source_problem = Problem.objects.filter(is_ai_source=True).first()
    problem_variant = ProblemVariant.objects.filter(generated_by=request.user).first()

    if problem_variant is not None:
        generated_user = problem_variant.generated_by
    else:
        generated_user = None

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
        'ai_source_problem': ai_source_problem,
        'problem_variant': problem_variant,
    })


# @login_required
def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    default_language = 'python'

    last_submission = None
    if request.user.is_authenticated:
        language = request.GET.get('language', default_language)
        last_submission = (
            Submission.objects.filter(user=request.user, problem=problem, language=language)
            .order_by('-created_at')
            .first()
        )
        submission_history = Submission.objects.filter(user=request.user, problem=problem).order_by('-created_at')
    else:
        language = default_language
        submission_history = Submission.objects.none()

    paginator = Paginator(submission_history, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    problem_solutions = ProblemSolution.objects.filter(problem=problem).first()
    problem_code = problem_solutions.code if problem_solutions else "No solutions available."

    return render(request, 'problems/problem_detail.html', {
        'problem': problem,
        'last_submission': last_submission,
        'selected_language': language,
        'submission_history': page_obj,
        'problem_code': problem_code,
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


@login_required
def generate_problem_variation(request):
    ai_source_problem = Problem.objects.filter(is_ai_source=True).first()
    problem = get_object_or_404(Problem, id=ai_source_problem.id)

    # Stop duplicate variants
    if ProblemVariant.objects.filter(generated_by=request.user).exists():
        messages.warning(request, "A variant already exists for this problem.")
        return redirect("problem_list")

    # 🔹 Call Gemini API
    api_key = settings.GEMINI_API_KEY  # put your API key in settings.py
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }

    prompt = f"""
        You are an AI assistant for a coding contest platform.

        Given this problem:
        Title: {problem.title}
        Description: {problem.description}

        Generate a new variation with:
        1. A very short title (1 to 6 words max, never longer).
        2. A rewritten description with RANDOM style. 
        - It could be detailed & direct.
        - Or a funny or dramatic story.
        - Or phrased as instructions.
        - Or a metaphorical situation.
        - Or a real-world scenario.
        - Or a puzzle or riddle.
        - Or a game-like challenge.
        - and min 40 words.
        - and max 200 words.
        - and also give some example input/output.
        - and explain question by using input/output format clearly.
        - Avoid repeating the original text.

        Each time, vary the style and wording. Do NOT always choose the same style.

        Return only valid JSON, no markdown, no explanation. 
        Example output format:
        {{
        "title": "Short Title",
        "description": "Creative or concise rewritten description"
        }}
    """



    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,   # higher = more randomness
            "top_p": 0.8,        # nucleus sampling
            "top_k": 40          # diverse sampling
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Extract text from Gemini response
        ai_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        if not ai_text:
            ai_text = '{"title": "Fallback", "description": "AI failed to generate."}'

        # --- Clean Gemini's markdown fences if present ---
        cleaned_text = ai_text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.strip("`")  # remove all backticks
            # remove optional "json" language hint
            cleaned_text = cleaned_text.replace("json\n", "", 1).replace("json", "", 1)
        # --- Parse JSON safely ---
        variation_data = {}
        try:
            variation_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("AI did not return valid JSON. Raw:", ai_text)
            variation_data = {
                "title": f"Variation of {problem.title}",
                "description": f"Alternate: {problem.description}",
            }

        variation_title = variation_data.get("title", f"Variation of {problem.title}")
        variation_description = variation_data.get("description", problem.description)

    except Exception as e:
        print("Gemini API Error:", e)
        variation_title = f"Variation of {problem.title}"
        variation_description = f"Alternate storyline: {problem.description}"


    except Exception as e:
        print("Gemini API Error:", e)
        variation_title = f"Variation of {problem.title}"
        variation_description = f"Alternate storyline: {problem.description}"

    # Save to DB
    ProblemVariant.objects.create(
        base_problem=problem,
        variant_title=variation_title,
        variant_description=variation_description,
        generated_by=request.user,
    )

    messages.success(request, "New AI-powered variation generated successfully! 🎉")
    return redirect("problem_list")


@login_required
def potd_problem(request):
    # Fetch today's AI-based problem (only 1 marked by admin)
    problem = Problem.objects.filter(is_ai_source=True).first()

    if not problem:
        messages.error(request, "No POTD problem available.")
        return redirect("problem_list")

    # Get the user's personal variant of this problem
    problem_variant = ProblemVariant.objects.filter(base_problem=problem, generated_by=request.user).first()

    if not problem_variant:
        messages.warning(request, "You have not generated your problem variation yet.")
        return redirect("problem_list")

    # Override problem title and description with the variant's version
    problem.title = problem_variant.variant_title
    problem.description = problem_variant.variant_description

    default_language = "python"
    language = request.GET.get("language", default_language)

    last_submission = (
        Submission.objects.filter(user=request.user, problem=problem, language=language)
        .order_by("-created_at")
        .first()
    )
    submission_history = Submission.objects.filter(user=request.user, problem=problem).order_by("-created_at")

    paginator = Paginator(submission_history, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    problem_code = "No solutions available."  # no predefined solution for POTD variants

    return render(request, "problems/problem_detail.html", {
        "problem": problem,
        "last_submission": last_submission,
        "selected_language": language,
        "submission_history": page_obj,
        "problem_code": problem_code,
    })
