# players/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PlayerStats

User = get_user_model()

@receiver(post_save, sender=User)
def create_player_stats(sender, instance, created, **kwargs):
    if created:
        PlayerStats.objects.create(user=instance)
