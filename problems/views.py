from django.shortcuts import render, get_object_or_404
from .models import Problem, Tag

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
    return render(request, 'problems/problem_detail.html', {'problem': problem})
