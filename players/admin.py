from django.contrib import admin
from .models import PlayerStats, Match, DuelRequest, MatchQueue, MatchHistory
# Register your models here.
admin.site.register(PlayerStats)
admin.site.register(Match)
admin.site.register(DuelRequest)
admin.site.register(MatchQueue)
admin.site.register(MatchHistory)

