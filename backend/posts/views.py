from django.db.models import Count
from rest_framework.decorators import action
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from comments.models import Comment
from comments.serializers import CommentTreeSerializer
from comments.utils import build_comment_tree
from .models import Post
from .serializers import PostSerializer


class PostViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return (
            Post.objects
            .select_related('author')
            .annotate(like_count=Count('likes', distinct=True))
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='comments/tree')
    def comments_tree(self, request, pk=None):
        post = self.get_object()
        comments = list(
            Comment.objects
            .filter(post=post)
            .select_related('author', 'parent')
            .annotate(like_count=Count('likes', distinct=True))
            .order_by('created_at')
        )
        roots = build_comment_tree(comments)
        serializer = CommentTreeSerializer(roots, many=True, context={'request': request})
        return Response(serializer.data)
