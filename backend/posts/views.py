from django.db import IntegrityError, transaction
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response
from rest_framework import status

from comments.models import Comment
from comments.serializers import CommentTreeSerializer
from comments.utils import build_comment_tree
from karma.models import KarmaEvent, SOURCE_POST_LIKE
from .models import Post, PostLike
from .serializers import PostSerializer

POST_LIKE_KARMA_POINTS = 5


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

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        post = self.get_object()
        if request.user == post.author:
            return Response(
                {'detail': 'Users cannot like their own post.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                post_like, created = PostLike.objects.get_or_create(user=request.user, post=post)
                if created:
                    KarmaEvent.objects.create(
                        recipient=post.author,
                        actor=request.user,
                        source_type=SOURCE_POST_LIKE,
                        points=POST_LIKE_KARMA_POINTS,
                        source_post_like=post_like,
                    )
        except IntegrityError:
            # Race-safe fallback: if concurrent insert happened, treat as already liked.
            created = False

        like_count = PostLike.objects.filter(post=post).count()
        return Response(
            {
                'liked': True,
                'created': created,
                'post_id': post.id,
                'like_count': like_count,
            }
        )

    @action(detail=True, methods=['delete'], url_path='like')
    def unlike(self, request, pk=None):
        post = self.get_object()
        with transaction.atomic():
            post_like = PostLike.objects.filter(user=request.user, post=post).first()
            if post_like:
                # Deleting the like also deletes the linked KarmaEvent via CASCADE.
                post_like.delete()
                deleted = True
            else:
                deleted = False
        like_count = PostLike.objects.filter(post=post).count()
        return Response(
            {
                'liked': False,
                'deleted': deleted,
                'post_id': post.id,
                'like_count': like_count,
            }
        )
