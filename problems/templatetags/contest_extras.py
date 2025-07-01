from problems.models import ContestRegistration
from django import template

register = template.Library()

@register.filter
def is_registered(contest, user):
    return ContestRegistration.objects.filter(user=user, contest=contest).exists()
