from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class LeaderboardUserSerializer(serializers.ModelSerializer):
    karma_24h = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'karma_24h']
