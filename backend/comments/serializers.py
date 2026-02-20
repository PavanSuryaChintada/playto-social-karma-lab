from django.db.models import Count
from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    like_count = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()

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
            'reply_count',
            'is_liked_by_me',
            'created_at',
        ]
        read_only_fields = ['author', 'created_at']

    def get_like_count(self, obj):
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.aggregate(total=Count('id'))['total']

    def get_reply_count(self, obj):
        if hasattr(obj, 'reply_count'):
            return obj.reply_count
        return obj.replies.aggregate(total=Count('id'))['total']

    def get_is_liked_by_me(self, obj):
        if hasattr(obj, 'is_liked_by_me'):
            return obj.is_liked_by_me
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()


class CommentTreeSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

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
            'is_liked_by_me',
            'created_at',
            'replies',
        ]

    def get_like_count(self, obj):
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.aggregate(total=Count('id'))['total']

    def get_is_liked_by_me(self, obj):
        if hasattr(obj, 'is_liked_by_me'):
            return obj.is_liked_by_me
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_replies(self, obj):
        children = getattr(obj, '_children', [])
        return CommentTreeSerializer(children, many=True, context=self.context).data
