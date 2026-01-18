from datetime import datetime
from extensions import db

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    subdeadit = db.Column(db.String(64), nullable=False, index=True)
    flair = db.Column(db.String(64))
    image_url = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Simple voting (for now just a count)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'post_id': self.id,
            'subdeadit': self.subdeadit,
            'author': f"u/{self.author.username}",
            'time_posted': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'flair': self.flair,
            'title': self.title,
            'body': self.body,
            'image_url': self.image_url,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'comments': [c.to_dict() for c in self.comments if c.parent_id is None]
        }

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    flair = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Voting
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    
    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    votes = db.relationship('Vote', backref='comment', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'comment_id': self.id,
            'author': f"u/{self.author.username}",
            'time_posted': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'flair': self.flair,
            'body': self.body,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'parent_comment_id': self.parent_id,
            'replies': [r.to_dict() for r in self.replies]
        }

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False)  # 1 for up, -1 for down
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_post_vote'),
        db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_vote'),
    )

