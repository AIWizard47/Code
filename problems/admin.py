from django.contrib import admin
from .models import Problem, TestCase, Tag
# Register your models here.
admin.site.register(Problem)
admin.site.register(TestCase)
admin.site.register(Tag)