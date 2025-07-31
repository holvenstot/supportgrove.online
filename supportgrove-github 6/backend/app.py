import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.story import db
from src.routes.stories import stories_bp
from src.routes.categories import categories_bp
from src.routes.comments import comments_bp
from src.routes.notifications import notifications_bp
from src.routes.sharing import sharing_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    
    # Enable CORS for all routes
    CORS(app, origins=['*'])
    
    # Database configuration
    database_path = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(stories_bp, url_prefix='/api')
    app.register_blueprint(categories_bp, url_prefix='/api')
    app.register_blueprint(comments_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(sharing_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'SupportGrove API is running'}
    
    # Serve React frontend (for single-server deployment)
    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        if path.startswith('api/'):
            return {'error': 'API endpoint not found'}, 404
        try:
            return send_from_directory(app.static_folder, path)
        except:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

