from django.db import models
from django.conf import settings


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    input_description = models.TextField()
    output_description = models.TextField()
    constraints = models.TextField()
    sample_input = models.TextField()
    sample_output = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    tags = models.ManyToManyField(Tag, related_name='problems')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)  # Show on UI or hidden

    def __str__(self):
        return f"TestCase for {self.problem.title}"

class Contest(models.Model):
    name = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    problems = models.ManyToManyField('Problem', related_name='contests_problems')

    def __str__(self):
        return self.name

class ContestSubmission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20)
    verdict = models.CharField(max_length=20)
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contest', 'problem')  # 1 accepted per problem per user

class ContestRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contest')

class ProblemSolution(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="solutions")
    code = models.TextField()
    language = models.CharField(max_length=20)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
# mostly story based or game based problems
class ProblemVariant(models.Model):
    base_problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="variants")
    variant_title = models.CharField(max_length=200)
    variant_description = models.TextField()
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Variant of {self.base_problem.title}"
