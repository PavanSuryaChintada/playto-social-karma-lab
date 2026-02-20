from django.conf import settings
from django.db import models
from django.db.models import Q

from comments.models import CommentLike
from posts.models import PostLike

SOURCE_POST_LIKE = 'post_like'
SOURCE_COMMENT_LIKE = 'comment_like'


class KarmaEvent(models.Model):
    SOURCE_POST_LIKE = SOURCE_POST_LIKE
    SOURCE_COMMENT_LIKE = SOURCE_COMMENT_LIKE
    SOURCE_CHOICES = [
        (SOURCE_POST_LIKE, 'Post Like'),
        (SOURCE_COMMENT_LIKE, 'Comment Like'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='karma_events_received',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='karma_events_performed',
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    points = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    source_post_like = models.OneToOneField(
        PostLike,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='karma_event',
    )
    source_comment_like = models.OneToOneField(
        CommentLike,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='karma_event',
    )

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['recipient', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(check=Q(points__gt=0), name='karma_points_gt_zero'),
            models.CheckConstraint(
                check=(
                    (Q(source_type='post_like') & Q(source_post_like__isnull=False) & Q(source_comment_like__isnull=True))
                    | (Q(source_type='comment_like') & Q(source_comment_like__isnull=False) & Q(source_post_like__isnull=True))
                ),
                name='karma_source_matches_type',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient_id} +{self.points} from {self.source_type}"
