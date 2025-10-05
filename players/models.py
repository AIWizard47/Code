from django.conf import settings
from django.db import models


class PlayerStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1200)   # ELO-style rating
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)  # winning streak
    league = models.CharField(max_length=20, default="Bronze")  # tier system

    def __str__(self):
        return f"{self.user.username} ({self.rating})"


class Match(models.Model):
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_as_p1"
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_as_p2"
    )
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches_won"
    )
    loser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matches_lost"
    )

    points_change = models.IntegerField(default=0)   # rating swing
    revenge_level = models.IntegerField(default=0)   # 0=normal,1=revenge,2=double revenge...

    def __str__(self):
        return f"{self.player1} vs {self.player2} ({self.problem})"


class MatchHistory(models.Model):
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="history_matches_as_p1"
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="history_matches_as_p2"
    )
    problem = models.ForeignKey("problems.Problem", on_delete=models.CASCADE)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_matches_won"
    )
    loser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_matches_lost"
    )

    points_change = models.IntegerField(default=0)   # rating swing
    revenge_level = models.IntegerField(default=0)   # 0=normal,1=revenge,2=double revenge...

    def __str__(self):
        return f"{self.player1} vs {self.player2} ({self.problem})"

class DuelRequest(models.Model):
    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenges_sent"
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenges_received"
    )
    finder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches_found"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_revenge = models.BooleanField(default=False)
    # Pending -> Accepted -> Finished OR Declined
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("finished", "Finished"),
        ],
        default="pending",
    )

class MatchQueue(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    last_ping = models.DateTimeField(auto_now=True)   # updated every 1s

