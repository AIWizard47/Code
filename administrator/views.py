from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from problems.models import Problem,Tag,TestCase, ProblemSolution
from users.models import UserRole, Role, ProblemUploader
from submissions.views import run
from django.views.decorators.csrf import csrf_exempt
import requests

# Create your views here.
def user_has_role(user, role_name: str) -> bool:
    return user.user_roles.filter(role__name=role_name).exists()

def home(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    if not (user_has_role(request.user, "Admin") or user_has_role(request.user, "Problem Uploader")):
        messages.error(request, "You do not have permission to access this page.")
        return redirect('/accounts/login/')
    tags = Tag.objects.all()
    role = UserRole.objects.filter(user=request.user).first()
    if user_has_role(request.user,"Admin") or user_has_role(request.user, "Problem Uploader"):
        try:
            uploader = ProblemUploader.objects.get(user=request.user)
            count_uploaded_problems = uploader.problems.count()
        except ProblemUploader.DoesNotExist:
            count_uploaded_problems = 0
    Problems = Problem.objects.all()
    
    context = {
        'tags': tags,
        'role': role.role.name if role else 'No Role',
        'count_uploaded_problems': count_uploaded_problems,
        'Problems': Problems,
    }
    return render(request, 'dashboard/home/index.html', context)

def upload_problem(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')

    if not (user_has_role(request.user, "Admin") or user_has_role(request.user, "Problem Uploader")):
        messages.error(request, "You do not have permission to access this page.")
        return redirect('/accounts/login/')
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get("title")
        slug = request.POST.get("slug")
        description = request.POST.get("description")
        input_description = request.POST.get("input_description")
        output_description = request.POST.get("output_description")
        constraints = request.POST.get("constraints")
        sample_input = request.POST.get("sample_input")
        sample_output = request.POST.get("sample_output")
        difficulty = request.POST.get("difficulty")
        tags = request.POST.getlist("tags")  # multiple checkboxes -> list

        if not title or not slug or not description or not input_description or not output_description or not constraints or not sample_input or not sample_output or not difficulty:
            messages.error(request, "Title, Slug, and Description are required.")
            return redirect('/administrator/dashboard/')
        
        # Create new Problem object
        problem = Problem.objects.create(
            title=title,
            slug=slug,
            description=description,
            input_description=input_description,
            output_description=output_description,
            constraints=constraints,
            sample_input=sample_input,
            sample_output=sample_output,
            difficulty=difficulty,
        )
        # Handle tags (assuming ManyToMany with Tag model)
        if tags:
            for tag_name in tags:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                problem.tags.add(tag)
        problem.save()
        problem_uploader, created = ProblemUploader.objects.get_or_create(user=request.user)
        problem_uploader.problems.add(problem)
        # Add success message
        messages.success(request, "Problem uploaded successfully!")
        return redirect('/administrator/dashboard/')  # or redirect to problem list/detail
    return redirect('/administrator/dashboard/')

def upload_testcase(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')

    if not (user_has_role(request.user, "Problem Uploader") or user_has_role(request.user, "Admin") or user_has_role(request.user, "TestCase Uploader")):
        messages.error(request, "You do not have permission to access this page.")
        return redirect('/accounts/login/')
    
    if request.method == 'POST':
        problem_id = request.POST.get("problem_id")
        input_data = request.POST.get("input_data")
        expected_output = request.POST.get("expected_output")
        is_sample = request.POST.get("is_sample") == "on"

        if not problem_id or not input_data or not expected_output:
            messages.error(request, "All fields are required.")
            return redirect('/administrator/dashboard/')

        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            messages.error(request, "Problem not found.")
            return redirect('/administrator/dashboard/')

        TestCase.objects.create(
            problem=problem,
            input_data=input_data,
            expected_output=expected_output,
            is_sample=is_sample
        )

        messages.success(request, "Testcase uploaded successfully!")
        return redirect('/administrator/dashboard/')

    return redirect('/administrator/dashboard/')

def generate_output(request):
    if request.user.is_authenticated == False:
        return redirect('/accounts/login/')
    if request.method == "POST":
        problem_id = request.POST.get("problem_id")
        input_data = request.POST.get("input_data")

        if not problem_id or not input_data:
            return JsonResponse({"success": False, "error": "Problem and input required."})

        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return JsonResponse({"success": False, "error": "Problem not found."})

        # Get solution code & language from DB
        print(problem_id, input_data)
        problem_solutions = ProblemSolution.objects.filter(problem=problem).first()
        if not problem_solutions:
            return JsonResponse({"success": False, "error": "No solution code available for this problem."})    
        solution_code = problem_solutions.code   # assuming this field exists
        language = problem_solutions.language # fallback
        print(language, solution_code)
        try:
            # Call the sandbox service directly
            response = requests.post("https://sandbox-production-ed09.up.railway.app/run/", json={
                "code": solution_code,
                "language": language,
                "input": input_data
            }, timeout=10)

            if response.status_code != 200:
                return JsonResponse({"success": False, "error": "Sandbox error: " + response.text})

            result = response.json()
            stdout = result.get("output", "")
            stderr = result.get("error", "")

            if stderr:
                return JsonResponse({"success": False, "error": stderr})

            return JsonResponse({"success": True, "output": stdout.strip()})

        except requests.exceptions.Timeout:
            return JsonResponse({"success": False, "error": "Sandbox request timed out."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request."})

def upload_solution(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')

    if not (user_has_role(request.user, "Admin") or user_has_role(request.user, "Problem Uploader")):
        messages.error(request, "You do not have permission to access this page.")
        return redirect('/accounts/login/')
    
    if request.method == "POST":
        problem_id = request.POST.get("problem")
        input_code = request.POST.get("input_code")
        language = request.POST.get("language")
        explanation = request.POST.get("explanation")

        if not problem_id or not input_code or not language or not explanation:
            messages.error(request, "All fields are required.")
            return redirect('/administrator/dashboard/')

        problem = get_object_or_404(Problem, id=problem_id)
        ProblemSolution.objects.create(
            problem=problem,
            code=input_code,
            language=language,
            explanation=explanation
        )

        messages.success(request, "Solution uploaded successfully!")
        return redirect('/administrator/dashboard/')

    return redirect('/administrator/dashboard/')