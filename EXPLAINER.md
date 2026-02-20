# EXPLAINER

## Deployment (Live)

- **Backend API:** [https://playto-social-karma-lab.onrender.com](https://playto-social-karma-lab.onrender.com) (Render)
- **Frontend:** [https://playto-social-karma-lab.vercel.app/](https://playto-social-karma-lab.vercel.app/) (Vercel)

See `README.md` for detailed deployment steps and environment variables.

## Test Accounts

Use these accounts to log in and explore the live demo (password for all: `SamplePass123!`):

- **alice** (alice@example.com)
- **bob** (bob@example.com)
- **carol** (carol@example.com)
- **dave** (dave@example.com)
- **eve** (eve@example.com)

---

## The Tree

### Data model for nested comments

Nested comments use an adjacency-list pattern:

- `Comment.parent` is a nullable self-referential foreign key.
- Root comments have `parent = null`.
- Replies point to another comment via `parent_id`.

### How tree serialization avoids N+1

Instead of recursively querying replies from the DB for each node:

1. Fetch all comments for a post in one queryset (`filter(post=...)`) with `select_related` and like-count annotations.
2. Build the tree in memory using `build_comment_tree(comments)`.
3. Serialize recursively from in-memory `_children`.

This keeps query count stable even with deep threads.

## The Math

### Last-24h leaderboard QuerySet

```python
window_start = timezone.now() - timedelta(hours=24)
queryset = (
    User.objects
    .annotate(
        karma_24h=Coalesce(
            Sum(
                "karma_events_received__points",
                filter=Q(karma_events_received__created_at__gte=window_start),
            ),
            Value(0),
        ),
    )
    .filter(karma_24h__gt=0)
    .order_by("-karma_24h", "id")[:5]
)
```

### Why this satisfies the requirement

- No `daily_karma` field on `User`.
- Karma is computed from immutable event history (`KarmaEvent`) at query time.
- Time window is dynamic and rolling (last 24h).

## The AI Audit

### Example bug introduced by AI

The initial AI-generated `KarmaEvent` model used:

```python
models.CheckConstraint(check=Q(...), name="...")
```

In this project environment, `CheckConstraint` expected `condition=...`, not `check=...`, causing server startup failure:

- `TypeError: CheckConstraint.__init__() got an unexpected keyword argument 'check'`

### Fix applied

- Replaced `check=` with `condition=` in `KarmaEvent` model constraints.
- Re-ran migrations and validated server startup.

This demonstrates the review/debug loop needed to catch AI-generated incompatibilities before shipping.
