from flask import Blueprint, request, jsonify
from src.models.story import db, Story
from src.models.comment import Comment
from src.models.sharing import SharedConversation, ForwardedEmail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re

sharing_bp = Blueprint('sharing', __name__)

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(recipient_email, subject, html_content, text_content=None):
    """Send email using SMTP (placeholder implementation)"""
    try:
        # This is a placeholder - in production, you'd use a service like SendGrid, AWS SES, etc.
        # For now, we'll just log the email content and mark as sent
        print(f"EMAIL SENT TO: {recipient_email}")
        print(f"SUBJECT: {subject}")
        print(f"CONTENT: {html_content}")
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

@sharing_bp.route('/stories/<int:story_id>/share-link', methods=['POST'])
def create_share_link(story_id):
    """Create a shareable link for a story conversation"""
    try:
        # Check if story exists
        story = Story.query.get(story_id)
        if not story:
            return jsonify({'error': 'Story not found'}), 404
        
        data = request.get_json() or {}
        shared_by = data.get('shared_by', '').strip() or None
        personal_message = data.get('personal_message', '').strip() or None
        expires_in_days = data.get('expires_in_days')
        
        # Create shared conversation
        shared_conversation = SharedConversation(
            story_id=story_id,
            shared_by=shared_by,
            personal_message=personal_message,
            expires_in_days=expires_in_days
        )
        
        db.session.add(shared_conversation)
        db.session.commit()
        
        # Return the shareable link
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/shared/{shared_conversation.share_id}"
        
        return jsonify({
            'success': True,
            'share_url': share_url,
            'share_id': shared_conversation.share_id,
            'shared_conversation': shared_conversation.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sharing_bp.route('/stories/<int:story_id>/forward/email', methods=['POST'])
def forward_via_email(story_id):
    """Forward a story conversation via email"""
    try:
        # Check if story exists
        story = Story.query.get(story_id)
        if not story:
            return jsonify({'error': 'Story not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data required'}), 400
        
        recipient_email = data.get('recipient_email', '').strip()
        sender_name = data.get('sender_name', '').strip() or None
        personal_message = data.get('personal_message', '').strip() or None
        
        # Validate email
        if not recipient_email or not validate_email(recipient_email):
            return jsonify({'error': 'Valid recipient email required'}), 400
        
        # Create shared conversation for the email
        shared_conversation = SharedConversation(
            story_id=story_id,
            shared_by=sender_name,
            personal_message=personal_message,
            expires_in_days=30  # Email links expire in 30 days
        )
        
        db.session.add(shared_conversation)
        db.session.flush()  # Get the ID without committing
        
        # Generate email content
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/shared/{shared_conversation.share_id}"
        
        sender_text = f"{sender_name} " if sender_name else "Someone "
        subject = f"{sender_text}shared a healing story with you from SupportGrove"
        
        # Create HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4a5d23;">Someone shared a healing story with you</h2>
                
                <p>Hi there,</p>
                
                <p><strong>{sender_text}</strong>thought you might find this story and conversation meaningful:</p>
                
                <div style="background-color: #f8f9f5; padding: 20px; border-left: 4px solid #4a5d23; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #4a5d23;">"{story.title}"</h3>
                    <p style="margin: 0; color: #666;">Category: {story.category}</p>
                    <p style="margin: 10px 0 0 0; font-size: 14px;">
                        {story.hashtags if story.hashtags else ''}
                    </p>
                </div>
                
                {f'<div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;"><p style="margin: 0; font-style: italic;">"{personal_message}"</p><p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">- {sender_name or "Anonymous"}</p></div>' if personal_message else ''}
                
                <div style="margin: 30px 0;">
                    <a href="{share_url}" style="background-color: #4a5d23; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Read the Full Conversation</a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p><strong>SupportGrove.Online</strong> - Anonymous Support Community</p>
                    <p style="font-style: italic;">"We are not alone. Our truth connects us. Our stories are powerful and healing."</p>
                    <p>This is a safe space for sharing experiences with addiction recovery, trauma healing, mental health, and life transitions.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        email_sent = send_email(recipient_email, subject, html_content)
        
        if email_sent:
            # Record the forwarded email
            forwarded_email = ForwardedEmail(
                story_id=story_id,
                recipient_email=recipient_email,
                sender_name=sender_name,
                personal_message=personal_message
            )
            
            db.session.add(forwarded_email)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Story forwarded successfully via email',
                'share_url': share_url,
                'forwarded_email': forwarded_email.to_dict()
            })
        else:
            db.session.rollback()
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sharing_bp.route('/shared/<share_id>')
def view_shared_conversation(share_id):
    """View a shared conversation thread"""
    try:
        # Find the shared conversation
        shared_conversation = SharedConversation.query.filter_by(share_id=share_id).first()
        if not shared_conversation:
            return jsonify({'error': 'Shared conversation not found'}), 404
        
        # Check if expired
        if shared_conversation.is_expired():
            return jsonify({'error': 'This shared conversation has expired'}), 410
        
        # Increment view count
        shared_conversation.increment_view_count()
        
        # Get the story and its comments
        story = shared_conversation.story
        comments = Comment.query.filter_by(story_id=story.id, parent_comment_id=None).order_by(Comment.created_at.asc()).all()
        
        # Build the response with full conversation
        story_data = story.to_dict()
        story_data['comments'] = []
        
        for comment in comments:
            comment_data = comment.to_dict()
            # Get replies for this comment
            replies = Comment.query.filter_by(parent_comment_id=comment.id).order_by(Comment.created_at.asc()).all()
            comment_data['replies'] = [reply.to_dict() for reply in replies]
            story_data['comments'].append(comment_data)
        
        return jsonify({
            'success': True,
            'shared_conversation': shared_conversation.to_dict(),
            'story': story_data,
            'meta': {
                'shared_by': shared_conversation.shared_by,
                'personal_message': shared_conversation.personal_message,
                'view_count': shared_conversation.view_count
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sharing_bp.route('/stories/<int:story_id>/sharing-stats')
def get_sharing_stats(story_id):
    """Get sharing statistics for a story"""
    try:
        story = Story.query.get(story_id)
        if not story:
            return jsonify({'error': 'Story not found'}), 404
        
        # Count shares and email forwards
        share_count = SharedConversation.query.filter_by(story_id=story_id).count()
        email_count = ForwardedEmail.query.filter_by(story_id=story_id).count()
        total_views = db.session.query(db.func.sum(SharedConversation.view_count)).filter_by(story_id=story_id).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'share_count': share_count,
                'email_forwards': email_count,
                'total_views': total_views,
                'total_forwards': share_count + email_count
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

