def build_comment_tree(comments):
    """
    Build a nested comment tree in memory from a flat list/queryset.
    This avoids recursive database access for each reply level.
    """
    comments_by_id = {}
    roots = []

    for comment in comments:
        comment._children = []
        comments_by_id[comment.id] = comment

    for comment in comments:
        if comment.parent_id and comment.parent_id in comments_by_id:
            comments_by_id[comment.parent_id]._children.append(comment)
        else:
            roots.append(comment)

    return roots
