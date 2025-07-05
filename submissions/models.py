from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem

class Submission(models.Model):
    STATUS_CHOICES = [
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20, default='python')
    created_at = models.DateTimeField(auto_now_add=True)
    verdict = models.CharField(max_length=20, choices=STATUS_CHOICES)
    output = models.TextField()
    error = models.TextField()
    
    def __str__(self):
        return f"TestCase for {self.problem.title} And User is {self.user.username} And {self.verdict}"
    
