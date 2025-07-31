from flask import Blueprint, request, jsonify
from src.models.story import db
from src.models.story import Story
from src.models.comment import Comment, CommentReaction, Notification
import uuid
from datetime import datetime

comments_bp = Blueprint('comments', __name__)

def get_anonymous_id():
    """Get or create anonymous ID from request headers"""
    anonymous_id = request.headers.get('X-Anonymous-ID')
    if not anonymous_id:
        anonymous_id = str(uuid.uuid4())
    return anonymous_id

def create_notification(recipient_id, notification_type, story_id=None, comment_id=None, trigger_id=None, message=None):
    """Create a notification for a user"""
    # Don't create self-notifications
    if recipient_id == trigger_id:
        return
    
    notification = Notification(
        recipient_anonymous_id=recipient_id,
        type=notification_type,
        story_id=story_id,
        comment_id=comment_id,
        trigger_anonymous_id=trigger_id,
        message=message
    )
    db.session.add(notification)

@comments_bp.route('/stories/<int:story_id>/comments', methods=['GET'])
def get_story_comments(story_id):
    """Get all comments for a story"""
    try:
        story = Story.query.get_or_404(story_id)
        
        # Get top-level comments (no parent)
        comments = Comment.query.filter_by(
            story_id=story_id, 
            parent_comment_id=None,
            is_deleted=False
        ).order_by(Comment.created_at.asc()).all()
        
        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments],
            'total_count': len(comments)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@comments_bp.route('/stories/<int:story_id>/comments', methods=['POST'])
def create_comment(story_id):
    """Create a new comment on a story"""
    try:
        data = request.get_json()
        anonymous_id = get_anonymous_id()
        
        # Validate required fields
        if not data.get('content'):
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Check if story exists
        story = Story.query.get_or_404(story_id)
        
        # Create comment
        comment = Comment(
            story_id=story_id,
            content=data['content'].strip(),
            pseudonym=data.get('pseudonym', '').strip() or None,
            anonymous_id=anonymous_id
        )
        
        db.session.add(comment)
        db.session.flush()  # Get the comment ID
        
        # Create notification for story author
        if story.anonymous_id != anonymous_id:
            message = f"Someone commented on your story '{story.title}'"
            create_notification(
                recipient_id=story.anonymous_id,
                notification_type='story_comment',
                story_id=story_id,
                comment_id=comment.id,
                trigger_id=anonymous_id,
                message=message
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict(),
            'anonymous_id': anonymous_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>/replies', methods=['POST'])
def create_reply(comment_id):
    """Create a reply to a comment"""
    try:
        data = request.get_json()
        anonymous_id = get_anonymous_id()
        
        # Validate required fields
        if not data.get('content'):
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Check if parent comment exists
        parent_comment = Comment.query.get_or_404(comment_id)
        
        # Create reply
        reply = Comment(
            story_id=parent_comment.story_id,
            parent_comment_id=comment_id,
            content=data['content'].strip(),
            pseudonym=data.get('pseudonym', '').strip() or None,
            anonymous_id=anonymous_id
        )
        
        db.session.add(reply)
        db.session.flush()  # Get the reply ID
        
        # Create notification for parent comment author
        if parent_comment.anonymous_id != anonymous_id:
            story = Story.query.get(parent_comment.story_id)
            message = f"Someone replied to your comment on '{story.title}'"
            create_notification(
                recipient_id=parent_comment.anonymous_id,
                notification_type='comment_reply',
                story_id=parent_comment.story_id,
                comment_id=reply.id,
                trigger_id=anonymous_id,
                message=message
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': reply.to_dict(),
            'anonymous_id': anonymous_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>/reactions', methods=['POST'])
def toggle_comment_reaction(comment_id):
    """Add or remove a reaction to a comment"""
    try:
        data = request.get_json()
        anonymous_id = get_anonymous_id()
        
        reaction_type = data.get('reaction_type')
        if reaction_type not in ['heart', 'hug', 'strength']:
            return jsonify({'success': False, 'error': 'Invalid reaction type'}), 400
        
        # Check if comment exists
        comment = Comment.query.get_or_404(comment_id)
        
        # Check if reaction already exists
        existing_reaction = CommentReaction.query.filter_by(
            comment_id=comment_id,
            anonymous_id=anonymous_id,
            reaction_type=reaction_type
        ).first()
        
        if existing_reaction:
            # Remove existing reaction
            db.session.delete(existing_reaction)
            action = 'removed'
        else:
            # Add new reaction
            reaction = CommentReaction(
                comment_id=comment_id,
                reaction_type=reaction_type,
                anonymous_id=anonymous_id
            )
            db.session.add(reaction)
            action = 'added'
            
            # Create notification for comment author
            if comment.anonymous_id != anonymous_id:
                story = Story.query.get(comment.story_id)
                reaction_emoji = {'heart': '❤️', 'hug': '🤗', 'strength': '✨'}[reaction_type]
                message = f"Someone reacted to your comment with {reaction_emoji}"
                create_notification(
                    recipient_id=comment.anonymous_id,
                    notification_type='comment_reaction',
                    story_id=comment.story_id,
                    comment_id=comment_id,
                    trigger_id=anonymous_id,
                    message=message
                )
        
        db.session.commit()
        
        # Get updated reaction counts
        updated_comment = Comment.query.get(comment_id)
        
        return jsonify({
            'success': True,
            'action': action,
            'reaction_counts': updated_comment.get_reaction_counts(),
            'anonymous_id': anonymous_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    """Update a comment (only by the author)"""
    try:
        data = request.get_json()
        anonymous_id = get_anonymous_id()
        
        comment = Comment.query.get_or_404(comment_id)
        
        # Check if user is the author
        if comment.anonymous_id != anonymous_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Update content
        if 'content' in data:
            comment.content = data['content'].strip()
            comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Delete a comment (only by the author)"""
    try:
        anonymous_id = get_anonymous_id()
        
        comment = Comment.query.get_or_404(comment_id)
        
        # Check if user is the author
        if comment.anonymous_id != anonymous_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Soft delete
        comment.is_deleted = True
        comment.content = '[Comment deleted]'
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

