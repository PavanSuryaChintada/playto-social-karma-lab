from django.db.models import Count
from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'author',
            'author_username',
            'post',
            'parent',
            'content',
            'like_count',
            'created_at',
        ]
        read_only_fields = ['author', 'created_at']

    def get_like_count(self, obj):
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.aggregate(total=Count('id'))['total']
