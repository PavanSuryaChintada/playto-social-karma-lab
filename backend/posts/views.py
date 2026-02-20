from django.db.models import Count
from rest_framework import mixins, permissions, viewsets

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
