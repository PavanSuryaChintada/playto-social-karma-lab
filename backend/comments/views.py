from django.db.models import Count
from django.db import IntegrityError, transaction
from rest_framework.decorators import action
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from karma.models import KarmaEvent, SOURCE_COMMENT_LIKE
from .models import Comment, CommentLike
from .serializers import CommentSerializer

COMMENT_LIKE_KARMA_POINTS = 1


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
                comment_like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
                if created:
                    KarmaEvent.objects.create(
                        recipient=comment.author,
                        actor=request.user,
                        source_type=SOURCE_COMMENT_LIKE,
                        points=COMMENT_LIKE_KARMA_POINTS,
                        source_comment_like=comment_like,
                    )
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
