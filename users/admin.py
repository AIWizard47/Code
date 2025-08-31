from django.contrib import admin
from .models import Role, UserRole, ProblemUploader
# Register your models here.

admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(ProblemUploader)