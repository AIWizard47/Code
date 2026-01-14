from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_users")

    class Meta:
        unique_together = ('user', 'role')
    def __str__(self):
        return f"{self.user.username} → {self.role.name}"
    
class ProblemUploader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="problem_uploader")
    problems = models.ManyToManyField(Problem, related_name="uploaded_by")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class UsersProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
#     achievements = models.TextField(blank=True)