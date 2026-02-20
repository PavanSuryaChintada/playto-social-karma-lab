from django.db.models import Count
from django.db import IntegrityError, transaction
from rest_framework.decorators import action
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from .models import Comment, CommentLike
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

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        comment = self.get_object()
        try:
            with transaction.atomic():
                _, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        except IntegrityError:
            created = False

        like_count = CommentLike.objects.filter(comment=comment).count()
        return Response(
            {
                'liked': True,
                'created': created,
                'comment_id': comment.id,
                'like_count': like_count,
            }
        )

    @action(detail=True, methods=['delete'], url_path='like')
    def unlike(self, request, pk=None):
        comment = self.get_object()
        deleted_count, _ = CommentLike.objects.filter(user=request.user, comment=comment).delete()
        like_count = CommentLike.objects.filter(comment=comment).count()
        return Response(
            {
                'liked': False,
                'deleted': deleted_count > 0,
                'comment_id': comment.id,
                'like_count': like_count,
            }
        )
