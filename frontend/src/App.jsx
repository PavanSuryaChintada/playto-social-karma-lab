import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

function buildHeaders(auth) {
  const headers = {
    "Content-Type": "application/json"
  };
  if (auth.username && auth.password) {
    headers.Authorization = `Basic ${btoa(`${auth.username}:${auth.password}`)}`;
  }
  return headers;
}

async function apiRequest(path, options = {}, auth = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...buildHeaders(auth),
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function CommentNode({ comment, onLikeComment, onReply, canWrite }) {
  const [replyText, setReplyText] = useState("");
  const [replyOpen, setReplyOpen] = useState(false);

  async function submitReply(event) {
    event.preventDefault();
    if (!replyText.trim()) return;
    await onReply(comment.id, replyText);
    setReplyText("");
    setReplyOpen(false);
  }

  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="text-sm text-slate-800">
        <span className="font-semibold">{comment.author_username}</span>: {comment.content}
      </div>
      <div className="mt-2 flex items-center gap-3 text-xs text-slate-600">
        <span>Likes: {comment.like_count}</span>
        <button
          className="rounded bg-indigo-600 px-2 py-1 text-white hover:bg-indigo-700"
          onClick={() => onLikeComment(comment.id, comment.is_liked_by_me)}
        >
          {comment.is_liked_by_me ? "Unlike" : "Like"}
        </button>
        <button
          className="rounded bg-slate-700 px-2 py-1 text-white hover:bg-slate-800"
          disabled={!canWrite}
          onClick={() => setReplyOpen((prev) => !prev)}
        >
          Reply
        </button>
      </div>
      {replyOpen && (
        <form className="mt-2 flex gap-2" onSubmit={submitReply}>
          <input
            className="w-full rounded border border-slate-300 p-1 text-sm"
            placeholder="Write a reply..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
          />
          <button className="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700" type="submit">
            Send
          </button>
        </form>
      )}
      {comment.replies?.length > 0 && (
        <div className="ml-4 mt-3 border-l border-slate-300 pl-3">
          {comment.replies.map((child) => (
            <CommentNode
              key={child.id}
              comment={child}
              onLikeComment={onLikeComment}
              onReply={onReply}
              canWrite={canWrite}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState({ username: "", password: "" });
  const [posts, setPosts] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [commentsByPost, setCommentsByPost] = useState({});
  const [expandedPosts, setExpandedPosts] = useState({});
  const [newPost, setNewPost] = useState("");
  const [newCommentByPost, setNewCommentByPost] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const canWrite = useMemo(() => auth.username && auth.password, [auth]);

  async function loadFeed() {
    setLoading(true);
    setError("");
    try {
      const [postData, leaderboardData] = await Promise.all([
        apiRequest("/posts/", {}, auth),
        apiRequest("/leaderboard/", {}, auth)
      ]);
      setPosts(postData);
      setLeaderboard(leaderboardData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFeed();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshPostComments(postId) {
    const tree = await apiRequest(`/posts/${postId}/comments/tree/`, {}, auth);
    setCommentsByPost((prev) => ({ ...prev, [postId]: tree }));
  }

  async function togglePostExpand(postId) {
    const isOpen = expandedPosts[postId];
    setExpandedPosts((prev) => ({ ...prev, [postId]: !isOpen }));
    if (!isOpen) {
      try {
        await refreshPostComments(postId);
      } catch (err) {
        setError(err.message);
      }
    }
  }

  async function handleLikePost(post) {
    try {
      const method = post.is_liked_by_me ? "DELETE" : "POST";
      await apiRequest(`/posts/${post.id}/like/`, { method }, auth);
      await loadFeed();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleLikeComment(commentId, postId, isLikedByMe) {
    try {
      const method = isLikedByMe ? "DELETE" : "POST";
      await apiRequest(`/comments/${commentId}/like/`, { method }, auth);
      await Promise.all([loadFeed(), refreshPostComments(postId)]);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreateComment(postId, parentId = null, text = null) {
    const content = (text ?? newCommentByPost[postId] ?? "").trim();
    if (!content) return;
    try {
      await apiRequest(
        "/comments/",
        {
          method: "POST",
          body: JSON.stringify({
            post: postId,
            parent: parentId,
            content
          })
        },
        auth
      );
      if (!parentId) {
        setNewCommentByPost((prev) => ({ ...prev, [postId]: "" }));
      }
      await Promise.all([loadFeed(), refreshPostComments(postId)]);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreatePost(event) {
    event.preventDefault();
    if (!newPost.trim()) return;
    try {
      await apiRequest(
        "/posts/",
        {
          method: "POST",
          body: JSON.stringify({ content: newPost })
        },
        auth
      );
      setNewPost("");
      await loadFeed();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 p-4 md:p-8">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <h1 className="mb-4 text-2xl font-bold text-slate-900">Community Feed</h1>
          <div className="mb-4 rounded-lg border border-slate-200 bg-white p-4">
            <p className="mb-3 text-sm text-slate-600">
              Add Basic Auth credentials to enable post/comment likes and post creation.
            </p>
            <div className="grid gap-2 md:grid-cols-3">
              <input
                className="rounded border border-slate-300 p-2"
                placeholder="Username"
                value={auth.username}
                onChange={(e) => setAuth((prev) => ({ ...prev, username: e.target.value }))}
              />
              <input
                type="password"
                className="rounded border border-slate-300 p-2"
                placeholder="Password"
                value={auth.password}
                onChange={(e) => setAuth((prev) => ({ ...prev, password: e.target.value }))}
              />
              <button
                className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-700"
                onClick={loadFeed}
              >
                Refresh Feed
              </button>
            </div>
          </div>

          <form onSubmit={handleCreatePost} className="mb-4 rounded-lg border border-slate-200 bg-white p-4">
            <textarea
              className="w-full rounded border border-slate-300 p-2"
              rows={3}
              placeholder="Write a post..."
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {canWrite ? "Ready to create post" : "Add auth to create posts"}
              </span>
              <button
                disabled={!canWrite}
                className="rounded bg-emerald-600 px-4 py-2 text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                type="submit"
              >
                Create Post
              </button>
            </div>
          </form>

          {error && <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          {loading ? (
            <p className="text-slate-600">Loading feed...</p>
          ) : (
            <div className="space-y-4">
              {posts.map((post) => (
                <article key={post.id} className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-sm text-slate-500">by {post.author_username}</p>
                  <p className="mt-2 text-slate-900">{post.content}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    <span>Likes: {post.like_count}</span>
                    <span>Comments: {post.comment_count}</span>
                    <button
                      className="rounded bg-indigo-600 px-3 py-1 text-white hover:bg-indigo-700"
                      onClick={() => handleLikePost(post)}
                    >
                      {post.is_liked_by_me ? "Unlike Post" : "Like Post"}
                    </button>
                    <button
                      className="rounded bg-slate-700 px-3 py-1 text-white hover:bg-slate-800"
                      onClick={() => togglePostExpand(post.id)}
                    >
                      {expandedPosts[post.id] ? "Hide Thread" : "View Thread"}
                    </button>
                  </div>
                  {expandedPosts[post.id] && (
                    <div className="mt-4">
                      <form
                        className="mb-3 flex gap-2"
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleCreateComment(post.id);
                        }}
                      >
                        <input
                          className="w-full rounded border border-slate-300 p-2 text-sm"
                          placeholder="Write a comment..."
                          value={newCommentByPost[post.id] || ""}
                          onChange={(e) =>
                            setNewCommentByPost((prev) => ({
                              ...prev,
                              [post.id]: e.target.value
                            }))
                          }
                        />
                        <button
                          disabled={!canWrite}
                          className="rounded bg-emerald-600 px-3 py-2 text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                          type="submit"
                        >
                          Comment
                        </button>
                      </form>
                      {(commentsByPost[post.id] || []).length === 0 ? (
                        <p className="text-sm text-slate-500">No comments yet.</p>
                      ) : (
                        commentsByPost[post.id].map((comment) => (
                          <CommentNode
                            key={comment.id}
                            comment={comment}
                            onLikeComment={(commentId, isLikedByMe) =>
                              handleLikeComment(commentId, post.id, isLikedByMe)
                            }
                            onReply={(parentId, text) => handleCreateComment(post.id, parentId, text)}
                            canWrite={canWrite}
                          />
                        ))
                      )}
                    </div>
                  )}
                </article>
              ))}
              {posts.length === 0 && <p className="text-slate-600">No posts yet.</p>}
            </div>
          )}
        </section>

        <aside className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-xl font-semibold text-slate-900">Top 5 (Last 24h)</h2>
          <ol className="space-y-2">
            {leaderboard.map((user, index) => (
              <li key={user.id} className="flex items-center justify-between rounded bg-slate-50 p-2">
                <span className="text-sm text-slate-700">
                  #{index + 1} {user.username}
                </span>
                <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                  {user.karma_24h} karma
                </span>
              </li>
            ))}
          </ol>
          {leaderboard.length === 0 && <p className="text-sm text-slate-500">No karma in the last 24h yet.</p>}
        </aside>
      </div>
    </div>
  );
}
