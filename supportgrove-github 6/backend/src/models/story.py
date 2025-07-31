from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#4A7C59')  # Grove Green default
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    stories = db.relationship('Story', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'story_count': len(self.stories)
        }

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anonymous_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Optional pseudonym for consistency across posts
    pseudonym = db.Column(db.String(50))
    
    # Hashtags for categorization
    hashtags = db.Column(db.Text)  # JSON string of hashtags
    
    # Guided sharing follow-up questions
    healing_process = db.Column(db.Text)  # "What has helped you through the healing process?"
    next_steps = db.Column(db.Text)  # "What is next in your life and recovery?"
    
    # Content metadata
    trigger_warning = db.Column(db.Boolean, default=False)
    trigger_tags = db.Column(db.Text)  # JSON string of trigger warning tags
    
    # Engagement metrics
    heart_count = db.Column(db.Integer, default=0)
    hug_count = db.Column(db.Integer, default=0)
    strength_count = db.Column(db.Integer, default=0)
    response_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    moderation_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('Response', backref='story', lazy=True, cascade='all, delete-orphan')
    reactions = db.relationship('Reaction', backref='story', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Story {self.title[:50]}...>'
    
    def to_dict(self, include_content=True):
        import json
        data = {
            'id': self.id,
            'title': self.title,
            'pseudonym': self.pseudonym or 'Anonymous',
            'category': self.category.to_dict() if self.category else None,
            'hashtags': json.loads(self.hashtags) if self.hashtags else [],
            'trigger_warning': self.trigger_warning,
            'trigger_tags': self.trigger_tags,
            'heart_count': self.heart_count,
            'hug_count': self.hug_count,
            'strength_count': self.strength_count,
            'response_count': self.response_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_content:
            data['content'] = self.content
            data['healing_process'] = self.healing_process
            data['next_steps'] = self.next_steps
            
        return data

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anonymous_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Optional pseudonym
    pseudonym = db.Column(db.String(50))
    
    # Response type
    response_type = db.Column(db.String(20), default='support')  # support, advice, experience
    
    # Engagement
    helpful_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Response to Story {self.story_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'pseudonym': self.pseudonym or 'Anonymous',
            'response_type': self.response_type,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # heart, hug, strength
    anonymous_id = db.Column(db.String(36), nullable=False)  # To prevent duplicate reactions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate reactions from same anonymous user
    __table_args__ = (db.UniqueConstraint('story_id', 'anonymous_id', 'reaction_type'),)
    
    def __repr__(self):
        return f'<Reaction {self.reaction_type} on Story {self.story_id}>'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)  # story, response
    content_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    reporter_anonymous_id = db.Column(db.String(36), nullable=False)
    
    # Moderation status
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    moderator_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Report {self.content_type} {self.content_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

