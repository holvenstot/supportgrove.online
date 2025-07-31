from flask import Blueprint, jsonify, request
from src.models.story import db, Story, Response, Reaction, Report, Category
from datetime import datetime
import uuid

stories_bp = Blueprint('stories', __name__)

@stories_bp.route('/stories', methods=['GET'])
def get_stories():
    """Get stories with optional filtering"""
    try:
        # Query parameters
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, heart_count, response_count
        
        # Build query
        query = Story.query.filter_by(is_approved=True, is_flagged=False)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Sorting
        if sort_by == 'heart_count':
            query = query.order_by(Story.heart_count.desc())
        elif sort_by == 'response_count':
            query = query.order_by(Story.response_count.desc())
        else:
            query = query.order_by(Story.created_at.desc())
        
        # Pagination
        stories = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'stories': [story.to_dict(include_content=False) for story in stories.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': stories.total,
                'pages': stories.pages,
                'has_next': stories.has_next,
                'has_prev': stories.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories', methods=['POST'])
def create_story():
    """Create a new story with guided sharing process"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['title', 'content', 'category_id']
        for field in required_fields:
            if not data or field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Verify category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({
                'success': False,
                'error': 'Invalid category'
            }), 400
        
        # Process hashtags
        import json
        hashtags = data.get('hashtags', [])
        if isinstance(hashtags, list):
            # Clean and validate hashtags
            clean_hashtags = []
            for tag in hashtags:
                if isinstance(tag, str) and tag.strip():
                    # Remove # if present and clean
                    clean_tag = tag.strip().lstrip('#').lower()
                    if clean_tag and len(clean_tag) <= 50:  # Limit hashtag length
                        clean_hashtags.append(clean_tag)
            hashtags_json = json.dumps(clean_hashtags[:10])  # Limit to 10 hashtags
        else:
            hashtags_json = json.dumps([])
        
        # Create story
        story = Story(
            title=data['title'],
            content=data['content'],
            category_id=data['category_id'],
            pseudonym=data.get('pseudonym', ''),
            hashtags=hashtags_json,
            healing_process=data.get('healing_process', ''),
            next_steps=data.get('next_steps', ''),
            trigger_warning=data.get('trigger_warning', False),
            trigger_tags=data.get('trigger_tags', '')
        )
        
        db.session.add(story)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'story': story.to_dict(),
            'message': 'Your story has been shared successfully. Thank you for contributing to our community.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    """Get a specific story with responses"""
    try:
        story = Story.query.filter_by(
            id=story_id, 
            is_approved=True, 
            is_flagged=False
        ).first_or_404()
        
        # Get responses
        responses = Response.query.filter_by(
            story_id=story_id,
            is_approved=True,
            is_flagged=False
        ).order_by(Response.created_at.asc()).all()
        
        story_data = story.to_dict()
        story_data['responses'] = [response.to_dict() for response in responses]
        
        return jsonify({
            'success': True,
            'story': story_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/<int:story_id>/responses', methods=['POST'])
def create_response(story_id):
    """Add a response to a story"""
    try:
        # Verify story exists
        story = Story.query.filter_by(
            id=story_id,
            is_approved=True,
            is_flagged=False
        ).first_or_404()
        
        data = request.get_json()
        
        if not data or 'content' not in data or not data['content']:
            return jsonify({
                'success': False,
                'error': 'Response content is required'
            }), 400
        
        response = Response(
            story_id=story_id,
            content=data['content'],
            pseudonym=data.get('pseudonym', ''),
            response_type=data.get('response_type', 'support')
        )
        
        db.session.add(response)
        
        # Update story response count
        story.response_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': response.to_dict(),
            'message': 'Response added successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/<int:story_id>/reactions', methods=['POST'])
def add_reaction(story_id):
    """Add or update a reaction to a story"""
    try:
        story = Story.query.filter_by(
            id=story_id,
            is_approved=True,
            is_flagged=False
        ).first_or_404()
        
        data = request.get_json()
        
        if not data or 'reaction_type' not in data or 'anonymous_id' not in data:
            return jsonify({
                'success': False,
                'error': 'reaction_type and anonymous_id are required'
            }), 400
        
        reaction_type = data['reaction_type']
        anonymous_id = data['anonymous_id']
        
        if reaction_type not in ['heart', 'hug', 'strength']:
            return jsonify({
                'success': False,
                'error': 'Invalid reaction type'
            }), 400
        
        # Check if reaction already exists
        existing_reaction = Reaction.query.filter_by(
            story_id=story_id,
            anonymous_id=anonymous_id,
            reaction_type=reaction_type
        ).first()
        
        if existing_reaction:
            return jsonify({
                'success': False,
                'error': 'You have already reacted with this type'
            }), 400
        
        # Create new reaction
        reaction = Reaction(
            story_id=story_id,
            reaction_type=reaction_type,
            anonymous_id=anonymous_id
        )
        
        db.session.add(reaction)
        
        # Update story reaction counts
        if reaction_type == 'heart':
            story.heart_count += 1
        elif reaction_type == 'hug':
            story.hug_count += 1
        elif reaction_type == 'strength':
            story.strength_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{reaction_type.title()} reaction added',
            'counts': {
                'heart_count': story.heart_count,
                'hug_count': story.hug_count,
                'strength_count': story.strength_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/<int:story_id>/reactions', methods=['DELETE'])
def remove_reaction(story_id):
    """Remove a reaction from a story"""
    try:
        data = request.get_json()
        
        if not data or 'reaction_type' not in data or 'anonymous_id' not in data:
            return jsonify({
                'success': False,
                'error': 'reaction_type and anonymous_id are required'
            }), 400
        
        reaction = Reaction.query.filter_by(
            story_id=story_id,
            anonymous_id=data['anonymous_id'],
            reaction_type=data['reaction_type']
        ).first_or_404()
        
        story = Story.query.get(story_id)
        
        # Update story reaction counts
        if reaction.reaction_type == 'heart':
            story.heart_count = max(0, story.heart_count - 1)
        elif reaction.reaction_type == 'hug':
            story.hug_count = max(0, story.hug_count - 1)
        elif reaction.reaction_type == 'strength':
            story.strength_count = max(0, story.strength_count - 1)
        
        db.session.delete(reaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{reaction.reaction_type.title()} reaction removed',
            'counts': {
                'heart_count': story.heart_count,
                'hug_count': story.hug_count,
                'strength_count': story.strength_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/reports', methods=['POST'])
def create_report():
    """Report inappropriate content"""
    try:
        data = request.get_json()
        
        required_fields = ['content_type', 'content_id', 'reason', 'anonymous_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        if data['content_type'] not in ['story', 'response']:
            return jsonify({
                'success': False,
                'error': 'Invalid content type'
            }), 400
        
        report = Report(
            content_type=data['content_type'],
            content_id=data['content_id'],
            reason=data['reason'],
            description=data.get('description', ''),
            reporter_anonymous_id=data['anonymous_id']
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully. Thank you for helping keep our community safe.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/search', methods=['GET'])
def search_stories():
    """Search stories by title, content, and hashtags"""
    try:
        import json
        
        query_text = request.args.get('q', '').strip()
        category_id = request.args.get('category_id', type=int)
        hashtag = request.args.get('hashtag', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not query_text and not hashtag:
            return jsonify({
                'success': False,
                'error': 'Search query or hashtag is required'
            }), 400
        
        # Build search query
        search_query = Story.query.filter_by(is_approved=True, is_flagged=False)
        
        # Add text search
        if query_text:
            search_query = search_query.filter(
                db.or_(
                    Story.title.contains(query_text),
                    Story.content.contains(query_text),
                    Story.healing_process.contains(query_text),
                    Story.next_steps.contains(query_text)
                )
            )
        
        # Add hashtag search
        if hashtag:
            clean_hashtag = hashtag.strip().lstrip('#').lower()
            search_query = search_query.filter(
                Story.hashtags.contains(f'"{clean_hashtag}"')
            )
        
        if category_id:
            search_query = search_query.filter_by(category_id=category_id)
        
        # Order by relevance (stories with query in title first, then by date)
        if query_text:
            search_query = search_query.order_by(
                Story.title.contains(query_text).desc(),
                Story.created_at.desc()
            )
        else:
            search_query = search_query.order_by(Story.created_at.desc())
        
        # Pagination
        results = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'query': query_text,
            'hashtag': hashtag,
            'stories': [story.to_dict(include_content=False) for story in results.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': results.total,
                'pages': results.pages,
                'has_next': results.has_next,
                'has_prev': results.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@stories_bp.route('/hashtags/trending', methods=['GET'])
def get_trending_hashtags():
    """Get trending hashtags based on recent usage"""
    try:
        import json
        from collections import Counter
        
        # Get stories from the last 30 days
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_stories = Story.query.filter(
            Story.created_at >= thirty_days_ago,
            Story.is_approved == True,
            Story.is_flagged == False,
            Story.hashtags.isnot(None)
        ).all()
        
        # Collect all hashtags
        all_hashtags = []
        for story in recent_stories:
            if story.hashtags:
                try:
                    hashtags = json.loads(story.hashtags)
                    all_hashtags.extend(hashtags)
                except:
                    continue
        
        # Count hashtag frequency
        hashtag_counts = Counter(all_hashtags)
        trending = [{'hashtag': tag, 'count': count} 
                   for tag, count in hashtag_counts.most_common(20)]
        
        return jsonify({
            'success': True,
            'trending_hashtags': trending
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/hashtags/<hashtag>/stories', methods=['GET'])
def get_stories_by_hashtag(hashtag):
    """Get stories filtered by a specific hashtag"""
    try:
        import json
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Clean the hashtag
        clean_hashtag = hashtag.strip().lstrip('#').lower()
        
        # Find stories containing this hashtag
        stories = Story.query.filter(
            Story.is_approved == True,
            Story.is_flagged == False,
            Story.hashtags.contains(f'"{clean_hashtag}"')
        ).order_by(Story.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'hashtag': clean_hashtag,
            'stories': [story.to_dict(include_content=False) for story in stories.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': stories.total,
                'pages': stories.pages,
                'has_next': stories.has_next,
                'has_prev': stories.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stories_bp.route('/stories/guided-questions', methods=['GET'])
def get_guided_questions():
    """Get the guided sharing questions for the frontend"""
    return jsonify({
        'success': True,
        'questions': {
            'healing_process': {
                'question': 'What has helped you through the healing process?',
                'placeholder': 'Share what strategies, people, activities, or insights have supported your healing journey...',
                'required': False
            },
            'next_steps': {
                'question': 'What is next in your life and recovery?',
                'placeholder': 'Share your hopes, goals, or next steps in your recovery journey...',
                'required': False
            }
        }
    })

