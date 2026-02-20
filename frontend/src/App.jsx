import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

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
    <div className="relative mt-3 ml-4 pl-4 border-l-2 border-white/10 border-l-indigo-500/40 hover:border-l-indigo-400/60 transition-all duration-300">
      <div className="rounded-lg border border-white/10 bg-slate-800/50 p-3 shadow-lg backdrop-blur-sm transition-all duration-300 hover:scale-[1.01]">
        <div className="text-sm text-slate-200">
          <span className="font-semibold text-indigo-300">{comment.author_username}</span>
          <span className="text-slate-400"> · </span>
          <span>{comment.content}</span>
        </div>
        <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
          <span>Likes: {comment.like_count}</span>
          <button
            className="rounded-md bg-indigo-600/80 px-2 py-1 text-white hover:bg-indigo-500 transition-all duration-300 hover:scale-105"
            onClick={() => onLikeComment(comment.id, comment.is_liked_by_me)}
          >
            {comment.is_liked_by_me ? "Unlike" : "Like"}
          </button>
          <button
            className="rounded-md bg-slate-700/80 px-2 py-1 text-slate-200 hover:bg-slate-600 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!canWrite}
            onClick={() => setReplyOpen((prev) => !prev)}
          >
            Reply
          </button>
        </div>
        {replyOpen && (
          <form className="mt-3 flex gap-2" onSubmit={submitReply}>
            <input
              className="w-full rounded-md border border-white/10 bg-slate-900/80 p-2 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
              placeholder="Write a reply..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
            />
            <button
              className="rounded-md bg-emerald-600/80 px-3 py-1.5 text-xs text-white hover:bg-emerald-500 transition-all duration-300 hover:scale-105"
              type="submit"
            >
              Send
            </button>
          </form>
        )}
      </div>
      {comment.replies?.length > 0 && (
        <div className="mt-2">
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
  const [authDropdownOpen, setAuthDropdownOpen] = useState(false);

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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-200 font-sans">
      {/* Sticky Header with glassmorphism */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-900/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 md:px-6">
          <h1 className="text-xl font-bold tracking-tight text-white">Playto Engine</h1>
          <div className="relative">
            <button
              onClick={() => setAuthDropdownOpen((prev) => !prev)}
              className="flex items-center gap-2 rounded-lg border border-white/10 bg-slate-800/50 px-4 py-2 text-sm transition-all duration-300 hover:scale-[1.02] hover:bg-slate-800/80"
            >
              <span
                className={`h-2 w-2 rounded-full ${canWrite ? "bg-emerald-500 shadow-lg shadow-emerald-500/50" : "bg-amber-500/80"}`}
              />
              {canWrite ? "Authenticated" : "Auth"}
            </button>
            {authDropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 rounded-lg border border-white/10 bg-slate-800/95 p-4 shadow-xl backdrop-blur-md">
                <p className="mb-3 text-xs text-slate-400">
                  Add Basic Auth credentials to enable post/comment likes and post creation.
                </p>
                <div className="space-y-2">
                  <input
                    className="w-full rounded-md border border-white/10 bg-slate-900/80 p-2 text-sm text-slate-200 placeholder-slate-500"
                    placeholder="Username"
                    value={auth.username}
                    onChange={(e) => setAuth((prev) => ({ ...prev, username: e.target.value }))}
                  />
                  <input
                    type="password"
                    className="w-full rounded-md border border-white/10 bg-slate-900/80 p-2 text-sm text-slate-200 placeholder-slate-500"
                    placeholder="Password"
                    value={auth.password}
                    onChange={(e) => setAuth((prev) => ({ ...prev, password: e.target.value }))}
                  />
                  <button
                    className="w-full rounded-md bg-indigo-600 px-3 py-2 text-sm text-white transition-all duration-300 hover:scale-[1.01] hover:bg-indigo-500"
                    onClick={() => {
                      loadFeed();
                      setAuthDropdownOpen(false);
                    }}
                  >
                    Refresh Feed
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content - 12 column grid */}
      <main className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Feed - 8 columns */}
          <section className="lg:col-span-8">
            <h2 className="mb-6 text-2xl font-bold text-white">Community Feed</h2>

            <form
              onSubmit={handleCreatePost}
              className="mb-6 rounded-xl border border-white/10 bg-slate-800/30 p-4 shadow-xl backdrop-blur-sm transition-all duration-300 hover:scale-[1.01]"
            >
              <textarea
                className="w-full rounded-lg border border-white/10 bg-slate-900/60 p-3 text-slate-200 placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
                rows={3}
                placeholder="Write a post..."
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
              />
              <div className="mt-3 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  {canWrite ? "Ready to create post" : "Add auth to create posts"}
                </span>
                <button
                  disabled={!canWrite}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
                  type="submit"
                >
                  Create Post
                </button>
              </div>
            </form>

            {error && (
              <div className="mb-6 rounded-lg border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {loading ? (
              <p className="text-slate-400">Loading feed...</p>
            ) : (
              <div className="space-y-6">
                {posts.map((post) => (
                  <article
                    key={post.id}
                    className="rounded-xl border border-white/10 bg-slate-800/30 p-5 shadow-xl backdrop-blur-sm transition-all duration-300 hover:scale-[1.01]"
                  >
                    <p className="text-sm text-slate-400">by {post.author_username}</p>
                    <p className="mt-2 text-slate-100">{post.content}</p>
                    <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
                      <span className="text-slate-400">Likes: {post.like_count}</span>
                      <span className="text-slate-400">Comments: {post.comment_count}</span>
                      <button
                        className="rounded-lg bg-indigo-600/80 px-3 py-1.5 text-white transition-all duration-300 hover:scale-[1.05] hover:bg-indigo-500"
                        onClick={() => handleLikePost(post)}
                      >
                        {post.is_liked_by_me ? "Unlike Post" : "Like Post"}
                      </button>
                      <button
                        className="rounded-lg bg-slate-700/80 px-3 py-1.5 text-slate-200 transition-all duration-300 hover:scale-[1.05] hover:bg-slate-600"
                        onClick={() => togglePostExpand(post.id)}
                      >
                        {expandedPosts[post.id] ? "Hide Thread" : "View Thread"}
                      </button>
                    </div>
                    {expandedPosts[post.id] && (
                      <div className="mt-5">
                        <form
                          className="mb-4 flex gap-2"
                          onSubmit={(e) => {
                            e.preventDefault();
                            handleCreateComment(post.id);
                          }}
                        >
                          <input
                            className="w-full rounded-lg border border-white/10 bg-slate-900/60 p-2 text-sm text-slate-200 placeholder-slate-500"
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
                            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white transition-all duration-300 hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-50"
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
                {posts.length === 0 && <p className="text-slate-500">No posts yet.</p>}
              </div>
            )}
          </section>

          {/* Leaderboard - 4 columns */}
          <aside className="lg:col-span-4">
            <div className="sticky top-24 rounded-xl border border-white/10 bg-slate-800/30 p-5 shadow-xl backdrop-blur-sm">
              <h2 className="mb-4 text-xl font-bold text-white">Trending</h2>
              <p className="mb-4 text-xs text-slate-400">Top 5 · Last 24h</p>
              <ol className="space-y-3">
                {leaderboard.map((user, index) => {
                  const rankStyle =
                    index === 0
                      ? "bg-amber-500/20 border-amber-400/40 text-amber-200"
                      : index === 1
                        ? "bg-slate-400/20 border-slate-300/40 text-slate-200"
                        : index === 2
                          ? "bg-amber-700/20 border-amber-600/40 text-amber-300"
                          : "bg-slate-800/50 border-white/5 text-slate-300";
                  return (
                    <li
                      key={user.id}
                      className={`flex items-center justify-between rounded-lg border p-3 transition-all duration-300 hover:scale-[1.02] ${rankStyle}`}
                    >
                      <span className="text-sm font-medium">
                        #{index + 1} {user.username}
                      </span>
                      <span className="rounded-md bg-indigo-500/20 px-2 py-1 text-xs font-semibold text-indigo-300">
                        {user.karma_24h} karma
                      </span>
                    </li>
                  );
                })}
              </ol>
              {leaderboard.length === 0 && <p className="text-sm text-slate-500">No karma in the last 24h yet.</p>}
            </div>
          </aside>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-white/10 bg-slate-900/50 py-6">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-slate-500 md:px-6">
          <p className="font-medium text-slate-400">Tech Stack</p>
          <p className="mt-1">Django & React</p>
          <p className="mt-2">Playto Community Feed · Threaded discussions & dynamic Karma leaderboard</p>
        </div>
      </footer>
    </div>
  );
}
