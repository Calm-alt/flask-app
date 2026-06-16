from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# =========================================
# USER MODEL (ENHANCED)
# =========================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(255), nullable=False)

    bio = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship(
        "Post",
        backref="author",
        lazy=True,
        cascade="all, delete"
    )

    likes = db.relationship(
        "Like",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


# =========================================
# POST MODEL (ENHANCED)
# =========================================
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    date_posted = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    content = db.Column(db.Text, nullable=False)

    # NEW: SEO / UX fields
    excerpt = db.Column(db.String(300), nullable=True)

    # RELATIONSHIPS
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    likes = db.relationship(
        "Like",
        backref="post",
        lazy=True,
        cascade="all, delete"
    )

    comments = db.relationship(
        "Comment",
        backref="post",
        lazy=True,
        cascade="all, delete"
    )

    def like_count(self):
        return len(self.likes)

    def comment_count(self):
        return len(self.comments)

    def reading_time(self):
        words = len(self.content.split())
        return max(1, words // 200)

    def __repr__(self):
        return f"Post('{self.title}')"


# =========================================
# LIKE SYSTEM (NEW)
# =========================================
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================
# COMMENT SYSTEM (NEW)
# =========================================
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    date_posted = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content[:20]}')"