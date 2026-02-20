from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions

from .serializers import LeaderboardUserSerializer

User = get_user_model()


class LeaderboardView(generics.ListAPIView):
    serializer_class = LeaderboardUserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        window_start = timezone.now() - timedelta(hours=24)
        return (
            User.objects
            .annotate(
                karma_24h=Coalesce(
                    Sum(
                        'karma_events_received__points',
                        filter=Q(karma_events_received__created_at__gte=window_start),
                    ),
                    Value(0),
                ),
            )
            .filter(karma_24h__gt=0)
            .order_by('-karma_24h', 'id')[:5]
        )
