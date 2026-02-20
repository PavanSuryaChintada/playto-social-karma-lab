from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comments.models import Comment, CommentLike
from posts.models import Post, PostLike

from .models import KarmaEvent, SOURCE_COMMENT_LIKE, SOURCE_POST_LIKE

User = get_user_model()


class LeaderboardApiTests(TestCase):
    def _create_post_like_event(self, recipient, actor, points=5, hours_ago=1):
        post = Post.objects.create(author=recipient, content=f'post by {recipient.username}')
        post_like = PostLike.objects.create(user=actor, post=post)
        event = KarmaEvent.objects.create(
            recipient=recipient,
            actor=actor,
            source_type=SOURCE_POST_LIKE,
            points=points,
            source_post_like=post_like,
        )
        KarmaEvent.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=hours_ago)
        )

    def _create_comment_like_event(self, recipient, actor, points=1, hours_ago=1):
        post = Post.objects.create(author=recipient, content=f'comment post {recipient.username}')
        comment = Comment.objects.create(author=recipient, post=post, content='root comment')
        comment_like = CommentLike.objects.create(user=actor, comment=comment)
        event = KarmaEvent.objects.create(
            recipient=recipient,
            actor=actor,
            source_type=SOURCE_COMMENT_LIKE,
            points=points,
            source_comment_like=comment_like,
        )
        KarmaEvent.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=hours_ago)
        )

    def test_leaderboard_counts_only_last_24_hours_and_returns_top_five(self):
        recipients = [User.objects.create_user(username=f'user{i}', password='pass1234') for i in range(1, 7)]
        actors = [User.objects.create_user(username=f'actor{i}', password='pass1234') for i in range(1, 7)]

        # user1 => 11 points (5 + 5 + 1)
        self._create_post_like_event(recipients[0], actors[0], points=5, hours_ago=2)
        self._create_post_like_event(recipients[0], actors[1], points=5, hours_ago=3)
        self._create_comment_like_event(recipients[0], actors[2], points=1, hours_ago=4)

        # user2 => 10 points
        self._create_post_like_event(recipients[1], actors[0], points=5, hours_ago=2)
        self._create_post_like_event(recipients[1], actors[1], points=5, hours_ago=2)

        # user3 => 6 points
        self._create_post_like_event(recipients[2], actors[2], points=5, hours_ago=1)
        self._create_comment_like_event(recipients[2], actors[3], points=1, hours_ago=1)

        # user4 => 5 points
        self._create_post_like_event(recipients[3], actors[4], points=5, hours_ago=1)

        # user5 => 1 point
        self._create_comment_like_event(recipients[4], actors[5], points=1, hours_ago=1)

        # user6 => old event (outside 24h), should be excluded
        self._create_post_like_event(recipients[5], actors[0], points=20, hours_ago=30)

        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 5)
        self.assertEqual(
            [row['username'] for row in data],
            ['user1', 'user2', 'user3', 'user4', 'user5'],
        )
        self.assertEqual([row['karma_24h'] for row in data], [11, 10, 6, 5, 1])
