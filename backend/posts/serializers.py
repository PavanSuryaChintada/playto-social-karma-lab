from rest_framework import serializers
from django.db.models import Count

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'author_username',
            'content',
            'like_count',
            'comment_count',
            'is_liked_by_me',
            'created_at',
        ]
        read_only_fields = ['author', 'created_at']

    def get_like_count(self, obj):
        # Prefer annotated value when queryset includes it.
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.aggregate(total=Count('id'))['total']

    def get_comment_count(self, obj):
        if hasattr(obj, 'comment_count'):
            return obj.comment_count
        return obj.comments.aggregate(total=Count('id'))['total']

    def get_is_liked_by_me(self, obj):
        if hasattr(obj, 'is_liked_by_me'):
            return obj.is_liked_by_me
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()
