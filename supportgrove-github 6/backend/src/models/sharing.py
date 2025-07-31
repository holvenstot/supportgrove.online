from datetime import datetime, timedelta
import secrets
import string
from src.models.story import db

class SharedConversation(db.Model):
    __tablename__ = 'shared_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    share_id = db.Column(db.String(32), unique=True, nullable=False)
    shared_by = db.Column(db.String(100))  # Optional sharer name
    personal_message = db.Column(db.Text)  # Optional message from sharer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    view_count = db.Column(db.Integer, default=0)
    
    # Relationship to story
    story = db.relationship('Story', backref='shared_conversations')
    
    def __init__(self, story_id, shared_by=None, personal_message=None, expires_in_days=None):
        self.story_id = story_id
        self.shared_by = shared_by
        self.personal_message = personal_message
        self.share_id = self.generate_share_id()
        if expires_in_days:
            self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    @staticmethod
    def generate_share_id():
        """Generate a unique, URL-safe share ID"""
        while True:
            # Generate a random 16-character string
            share_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            # Check if it's unique
            if not SharedConversation.query.filter_by(share_id=share_id).first():
                return share_id
    
    def is_expired(self):
        """Check if the shared conversation has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def increment_view_count(self):
        """Increment the view count when someone accesses the shared conversation"""
        self.view_count += 1
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'story_id': self.story_id,
            'share_id': self.share_id,
            'shared_by': self.shared_by,
            'personal_message': self.personal_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'view_count': self.view_count,
            'is_expired': self.is_expired()
        }

class ForwardedEmail(db.Model):
    __tablename__ = 'forwarded_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    sender_name = db.Column(db.String(100))
    personal_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')
    
    # Relationship to story
    story = db.relationship('Story', backref='forwarded_emails')
    
    def __init__(self, story_id, recipient_email, sender_name=None, personal_message=None):
        self.story_id = story_id
        self.recipient_email = recipient_email
        self.sender_name = sender_name
        self.personal_message = personal_message
    
    def to_dict(self):
        return {
            'id': self.id,
            'story_id': self.story_id,
            'recipient_email': self.recipient_email,
            'sender_name': self.sender_name,
            'personal_message': self.personal_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status
        }

