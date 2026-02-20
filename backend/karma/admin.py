from django.contrib import admin

from .models import KarmaEvent


@admin.register(KarmaEvent)
class KarmaEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'actor', 'source_type', 'points', 'created_at']
    list_filter = ['source_type', 'created_at']
    search_fields = ['recipient__username', 'actor__username']
