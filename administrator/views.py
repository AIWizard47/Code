from django.shortcuts import render,redirect
from django.contrib import messages
from problems.models import Problem,Tag
from users.models import UserRole, Role, ProblemUploader

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
    context = {
        'tags': tags,
        'role': role.role.name if role else 'No Role',
        'count_uploaded_problems': count_uploaded_problems,
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

        print(title)
        if not title or not slug or not description or not input_description or not output_description or not constraints or not sample_input or not sample_output or not difficulty:
            messages.error(request, "Title, Slug, and Description are required.")
            print(messages)
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
        # Add success message
        messages.success(request, "Problem uploaded successfully!")
        return redirect('/administrator/dashboard/')  # or redirect to problem list/detail
    return redirect('/administrator/dashboard/')

def upload_testcase(request):
    pass