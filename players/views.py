import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from players.models import PlayerStats, Match, DuelRequest, MatchQueue
from problems.models import Problem
from django.http import JsonResponse
from django.db import models
from datetime import timedelta
from django.utils import timezone


@login_required
def match_room(request, match_id):
    """Display the match room"""
    match = get_object_or_404(Match, id=match_id)

    # Security: only participants can enter
    if request.user not in [match.player1, match.player2]:
        return render(request, "duels/not_allowed.html")

    return render(request, "duels/room.html", {
        "match": match,
    })


@login_required
def find_match(request):
    """Auto matchmaking: either wait or start a match instantly"""
    me = request.user
    my_stats = PlayerStats.objects.get(user=me)

    # Try to find opponent already waiting
    opponent_entry = (
        MatchQueue.objects
        .exclude(user=me)
        .filter(rating__gte=my_stats.rating - 100, rating__lte=my_stats.rating + 100)
        .order_by("joined_at")
        .first()
    )
    check_in_match_player1_1 = Match.objects.filter(player1=me).exists()
    check_in_match_player1_2 = Match.objects.filter(player2=me).exists()
    if opponent_entry:
        check_in_match_player2_1 = Match.objects.filter(player1=opponent_entry.user).exists()
        check_in_match_player2_2 = Match.objects.filter(player2=opponent_entry.user).exists()
                
    print(opponent_entry)
    
    # print(check_in_match_player1, check_in_match_player2)
    if opponent_entry and not check_in_match_player1_1  and not check_in_match_player1_2 and not check_in_match_player2_1 and not check_in_match_player2_2:
        opponent = opponent_entry.user
        opponent_entry.delete()
        MatchQueue.objects.filter(user=me).delete()

        # Pick a problem (random for now)
        problem = Problem.objects.order_by("?").first()

        # Create match instantly
        match = Match.objects.create(
            player1=me,
            player2=opponent,
            problem=problem,
        )

        return redirect("duel_room", match_id=match.id)

    else:
        # No opponent found → add me to queue
        MatchQueue.objects.update_or_create(
            user=me, defaults={"rating": my_stats.rating}
        )
        return render(request, "duels/waiting.html")

def is_in_match(user):
    return DuelRequest.objects.filter(
        models.Q(challenger=user) | models.Q(opponent=user),
        status__in=["pending", "accepted"]
    ).exists()


@login_required
def check_for_match(request):
    me = request.user

    # 1. Remove inactive users (>3 sec no ping)
    cutoff = timezone.now() - timedelta(seconds=3)
    MatchQueue.objects.filter(last_ping__lt=cutoff).delete()

    # 2. If I am still in queue, refresh my heartbeat
    MatchQueue.objects.filter(user=me).update(last_ping=timezone.now())

    # 3. Check if I got matched already
    match = (
        Match.objects.filter(player1=me)
        .order_by("-started_at")
        .first()
        or Match.objects.filter(player2=me)
        .order_by("-started_at")
        .first()
    )

    return JsonResponse({"match_id": match.id if match else None})


@login_required
def accept_duel(request, duel_id):
    """Opponent accepts a duel request, match begins"""
    duel = get_object_or_404(DuelRequest, id=duel_id, opponent=request.user)

    if duel.accepted:
        return redirect("duel_room", duel_id=duel.id)

    duel.accepted = True
    duel.save()

    # Pick a random problem for this duel
    problem = Problem.objects.order_by("?").first()

    # Create a match record
    match = Match.objects.create(
        player1=duel.challenger,
        player2=duel.opponent,
        problem=problem,
        revenge_level=1 if duel.is_revenge else 0,
    )

    return redirect("duel_room", match_id=match.id)


@login_required
def duel_room(request, match_id):
    """The actual duel interface where both players solve the problem"""
    match = get_object_or_404(Match, id=match_id)

    # Ensure only participants can access
    if request.user not in [match.player1, match.player2]:
        return redirect("dashboard")
    print(match)
    return render(request, "duels/duel.html", {
        "match": match,
        "problem": match.problem,
        'player1': match.player1.username,
        'player2': match.player2.username,
    })



@login_required
def finish_duel(request, match_id, winner_id):
    """End the duel, update ratings + stats"""
    match = get_object_or_404(Match, id=match_id)

    winner = get_object_or_404(PlayerStats, user_id=winner_id)
    loser = winner.user
    if match.player1 == winner.user:
        loser = match.player2
    else:
        loser = match.player1

    loser_stats = PlayerStats.objects.get(user=loser)

    # Rating logic (simplified)
    rating_change = 30
    winner.rating += rating_change
    loser_stats.rating -= rating_change

    winner.wins += 1
    loser_stats.losses += 1

    # streaks
    winner.streak += 1
    loser_stats.streak = 0

    winner.save()
    loser_stats.save()

    # update match
    match.finished_at = timezone.now()
    match.winner = winner.user
    match.loser = loser
    match.points_change = rating_change
    match.save()

    return render(request, "duels/result.html", {
        "match": match,
        "winner": winner.user,
        "loser": loser,
        "rating_change": rating_change,
    })


@login_required
def request_revenge(request, match_id):
    """Loser can challenge winner again"""
    match = get_object_or_404(Match, id=match_id)

    DuelRequest.objects.create(
        challenger=request.user,
        opponent=match.winner,
        is_revenge=True,
    )

    return render(request, "duels/revenge_sent.html", {
        "opponent": match.winner,
    })
