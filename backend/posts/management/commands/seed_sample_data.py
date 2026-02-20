"""
Seed the database with sample users, posts, comments, likes, and karma.
Run: python manage.py seed_sample_data
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from comments.models import Comment, CommentLike
from karma.models import KarmaEvent, SOURCE_POST_LIKE, SOURCE_COMMENT_LIKE
from posts.management.commands.add_sample_users import SAMPLE_USERS, DEFAULT_PASSWORD
from posts.models import Post, PostLike

User = get_user_model()

POST_LIKE_KARMA = 5
COMMENT_LIKE_KARMA = 1


SAMPLE_POSTS = [
    {"author": "alice", "content": "Just shipped a new feature! 🚀 Excited to share it with the community."},
    {"author": "bob", "content": "Looking for feedback on our API design. What would make it easier to use?"},
    {"author": "carol", "content": "Weekend hack: built a tiny CLI tool for karma stats. Open to contributions!"},
    {"author": "dave", "content": "Great discussion in the thread yesterday. Thanks everyone for the ideas."},
    {"author": "eve", "content": "New to the community – hi everyone! Where do I start?"},
]

# (author, content, parent_author_username or None for root, post_index)
SAMPLE_COMMENTS = [
    ("bob", "Congrats Alice! Can't wait to try it.", None, 0),
    ("carol", "Same here! 🎉", None, 0),
    ("dave", "Nice work.", None, 0),
    ("eve", "What's the tech stack?", None, 0),
    ("alice", "We use Django + React", "eve", 0),
    ("alice", "REST endpoints might help – have you tried OpenAPI?", None, 1),
    ("carol", "I'd love GraphQL for nested queries", None, 1),
    ("bob", "GraphQL is on the roadmap!", "carol", 1),
    ("eve", "I'll check out the repo", None, 2),
    ("alice", "Welcome Eve! Start with the pinned post.", None, 4),
]


def ensure_users(cmd):
    """Create sample users if they don't exist."""
    for data in SAMPLE_USERS:
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults={"email": data["email"]},
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            cmd.stdout.write(f"Created user: {user.username}")
    return {u["username"]: User.objects.get(username=u["username"]) for u in SAMPLE_USERS}


class Command(BaseCommand):
    help = "Seed users, posts, comments, likes, and karma for testing"

    def handle(self, *args, **options):
        with transaction.atomic():
            users = ensure_users(self)
            self.stdout.write("")

            posts = []
            for i, p in enumerate(SAMPLE_POSTS):
                author = users[p["author"]]
                post = Post.objects.create(author=author, content=p["content"])
                posts.append(post)
                self.stdout.write(f"Created post {post.id} by {author.username}")

            self.stdout.write("")

            comments_by_key = {}  # (post_idx, parent_author or "") -> comment
            for author_name, content, parent_author, post_idx in SAMPLE_COMMENTS:
                author = users[author_name]
                post = posts[post_idx]
                parent = None
                if parent_author:
                    parent = comments_by_key.get((post_idx, parent_author))
                comment = Comment.objects.create(
                    author=author, post=post, parent=parent, content=content
                )
                comments_by_key[(post_idx, author_name)] = comment
                self.stdout.write(f"Created comment on post {post.id} by {author.username}")

            self.stdout.write("")

            usernames = list(users.keys())
            for post in posts:
                author_name = post.author.username
                likers = [u for u in usernames if u != author_name]
                for liker_name in likers[:3]:
                    liker = users[liker_name]
                    pl, created = PostLike.objects.get_or_create(user=liker, post=post)
                    if created:
                        KarmaEvent.objects.create(
                            recipient=post.author,
                            actor=liker,
                            source_type=SOURCE_POST_LIKE,
                            points=POST_LIKE_KARMA,
                            source_post_like=pl,
                        )
                self.stdout.write(f"Added post likes for post {post.id}")

            all_comments = list(Comment.objects.select_related("author").all())
            for comment in all_comments:
                author_name = comment.author.username
                likers = [u for u in usernames if u != author_name]
                for liker_name in likers[:2]:
                    liker = users[liker_name]
                    cl, created = CommentLike.objects.get_or_create(
                        user=liker, comment=comment
                    )
                    if created:
                        KarmaEvent.objects.create(
                            recipient=comment.author,
                            actor=liker,
                            source_type=SOURCE_COMMENT_LIKE,
                            points=COMMENT_LIKE_KARMA,
                            source_comment_like=cl,
                        )
                self.stdout.write(f"Added comment likes for comment {comment.id}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Log in with any username and password: {DEFAULT_PASSWORD}"
            )
        )
        self.stdout.write(
            "Users: alice, bob, carol, dave, eve"
        )
