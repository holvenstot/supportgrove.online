from flask import Blueprint, jsonify, request
from src.models.story import db, Category

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with story counts"""
    try:
        categories = Category.query.all()
        return jsonify({
            'success': True,
            'categories': [category.to_dict() for category in categories]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new category (admin function)"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        # Check if category already exists
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Category already exists'
            }), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            color=data.get('color', '#4A7C59'),
            icon=data.get('icon', '')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a specific category"""
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'category': category.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/seed', methods=['POST'])
def seed_categories():
    """Seed initial categories for the platform"""
    try:
        default_categories = [
            {
                'name': 'Addiction Recovery',
                'description': 'Stories and support for overcoming substance abuse and behavioral addictions',
                'color': '#4A7C59',
                'icon': 'recovery'
            },
            {
                'name': 'Trauma & Healing',
                'description': 'Experiences with PTSD, childhood trauma, abuse recovery, racial trauma, sexism, religious abuse, gender fluidity shaming, and multigenerational family dysfunctionality',
                'color': '#87CEEB',
                'icon': 'healing'
            },
            {
                'name': 'Mental Health',
                'description': 'Depression, anxiety, bipolar disorder, and other mental health journeys',
                'color': '#E6E6FA',
                'icon': 'mental-health'
            },
            {
                'name': 'Life Transitions',
                'description': 'Displacement, loss, major life changes, and adaptation',
                'color': '#FFB6C1',
                'icon': 'transition'
            },
            {
                'name': 'Relationship Recovery',
                'description': 'Healing from domestic violence, toxic relationships, and emotional abuse',
                'color': '#8FBC8F',
                'icon': 'relationship'
            },
            {
                'name': 'Self-Care & Wellness',
                'description': 'Coping strategies, mindfulness, and personal growth',
                'color': '#FFD700',
                'icon': 'wellness'
            }
        ]
        
        created_categories = []
        for cat_data in default_categories:
            # Check if category already exists
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                created_categories.append(cat_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created_categories)} categories',
            'created': created_categories
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

