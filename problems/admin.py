from django.contrib import admin
from .models import Problem, TestCase, Tag, Contest, ContestSubmission, ContestRegistration
# Register your models here.
admin.site.register(Problem)
admin.site.register(TestCase)
admin.site.register(Tag)
admin.site.register(Contest)
admin.site.register(ContestSubmission)
admin.site.register(ContestRegistration)
