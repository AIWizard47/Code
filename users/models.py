from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem
from django.db.models.signals import post_save
from django.dispatch import receiver

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

# models.py

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    location = models.CharField(max_length=100, blank=True, default='Unknown')
    bio = models.TextField(blank=True, default='')
    rank = models.CharField(max_length=50, blank=True, default='Beginner')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Auto-create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()