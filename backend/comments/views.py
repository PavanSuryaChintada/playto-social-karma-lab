from django.db.models import Count
from rest_framework import mixins, permissions, viewsets

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = (
            Comment.objects
            .select_related('author', 'post', 'parent')
            .annotate(like_count=Count('likes', distinct=True))
            .order_by('created_at')
        )
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
