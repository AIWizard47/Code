from django.contrib import admin
from .models import Problem, TestCase, Tag, Contest, ContestSubmission, ContestRegistration, ProblemSolution, ProblemVariant
# Register your models here.
admin.site.register(Problem)
admin.site.register(TestCase)
admin.site.register(Tag)
admin.site.register(Contest)
admin.site.register(ContestSubmission)
admin.site.register(ContestRegistration)
admin.site.register(ProblemSolution)
admin.site.register(ProblemVariant)