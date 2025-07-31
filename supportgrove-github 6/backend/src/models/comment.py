from datetime import datetime
from src.models.story import db

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    pseudonym = db.Column(db.String(100), nullable=True)
    anonymous_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    story = db.relationship('Story', backref='comments')
    parent_comment = db.relationship('Comment', remote_side=[id], backref='replies')
    reactions = db.relationship('CommentReaction', backref='comment', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'story_id': self.story_id,
            'parent_comment_id': self.parent_comment_id,
            'content': self.content,
            'pseudonym': self.pseudonym or 'Anonymous',
            'anonymous_id': self.anonymous_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_deleted': self.is_deleted,
            'reply_count': len([r for r in self.replies if not r.is_deleted]),
            'reaction_counts': self.get_reaction_counts(),
            'replies': [reply.to_dict() for reply in self.replies if not reply.is_deleted]
        }
    
    def get_reaction_counts(self):
        """Get count of each reaction type for this comment"""
        reaction_counts = {'heart': 0, 'hug': 0, 'strength': 0}
        for reaction in self.reactions:
            if reaction.reaction_type in reaction_counts:
                reaction_counts[reaction.reaction_type] += 1
        return reaction_counts

class CommentReaction(db.Model):
    __tablename__ = 'comment_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # 'heart', 'hug', 'strength'
    anonymous_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate reactions
    __table_args__ = (db.UniqueConstraint('comment_id', 'anonymous_id', 'reaction_type'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'reaction_type': self.reaction_type,
            'anonymous_id': self.anonymous_id,
            'created_at': self.created_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_anonymous_id = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'story_comment', 'comment_reply', 'comment_reaction'
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    trigger_anonymous_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    story = db.relationship('Story', backref='notifications')
    comment = db.relationship('Comment', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'recipient_anonymous_id': self.recipient_anonymous_id,
            'type': self.type,
            'story_id': self.story_id,
            'comment_id': self.comment_id,
            'trigger_anonymous_id': self.trigger_anonymous_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'story_title': self.story.title if self.story else None
        }

