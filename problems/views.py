from django.shortcuts import render, get_object_or_404
from .models import Problem

def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems': problems})

def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    return render(request, 'problems/problem_detail.html', {'problem': problem})
