from django.db import models
from django.conf import settings

from posts.models import Post


class Comment(models.Model):
    """A comment on a post, or a reply to another comment (nested threads)."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post_id}"


class CommentLike(models.Model):
    """A like on a comment. One user can like a comment only once."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes',
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'comment'], name='unique_user_comment_like'),
        ]

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment_id}"
