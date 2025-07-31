from flask import Blueprint, request, jsonify
from src.models.story import db
from src.models.comment import Notification
import uuid

notifications_bp = Blueprint('notifications', __name__)

def get_anonymous_id():
    """Get or create anonymous ID from request headers"""
    anonymous_id = request.headers.get('X-Anonymous-ID')
    if not anonymous_id:
        anonymous_id = str(uuid.uuid4())
    return anonymous_id

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for the current user"""
    try:
        anonymous_id = get_anonymous_id()
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Build query
        query = Notification.query.filter_by(recipient_anonymous_id=anonymous_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'notifications': [notification.to_dict() for notification in notifications],
            'total_count': total_count,
            'unread_count': Notification.query.filter_by(
                recipient_anonymous_id=anonymous_id, 
                is_read=False
            ).count(),
            'anonymous_id': anonymous_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread notifications for the current user"""
    try:
        anonymous_id = get_anonymous_id()
        
        unread_count = Notification.query.filter_by(
            recipient_anonymous_id=anonymous_id,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'anonymous_id': anonymous_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        anonymous_id = get_anonymous_id()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_anonymous_id=anonymous_id
        ).first_or_404()
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/notifications/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    try:
        anonymous_id = get_anonymous_id()
        
        # Update all unread notifications for this user
        updated_count = Notification.query.filter_by(
            recipient_anonymous_id=anonymous_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Marked {updated_count} notifications as read'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        anonymous_id = get_anonymous_id()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_anonymous_id=anonymous_id
        ).first_or_404()
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/notifications/cleanup', methods=['POST'])
def cleanup_old_notifications():
    """Clean up old notifications (older than 30 days)"""
    try:
        from datetime import datetime, timedelta
        
        # Delete notifications older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_count = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} old notifications'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

