from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import config
import os
import logging

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Determine configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Handle Render environment
    if os.getenv('RENDER'):
        config_name = 'render'
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    try:
        db.init_app(app)
        jwt.init_app(app)
        CORS(app, origins=app.config['CORS_ORIGINS'])
        migrate.init_app(app, db)
        
        app.logger.info(f"Initialized with config: {config_name}")
        app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {e}")
        # Don't fail completely, let the app start and show the error in health check
    
    # JWT identity loader
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            from app.models.user import User
            identity = jwt_data["sub"]
            return User.query.get(int(identity))
        except Exception as e:
            app.logger.error(f"JWT user lookup failed: {e}")
            return None
    
    # Create upload folder if it doesn't exist
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        app.logger.info(f"Upload folder ready: {app.config['UPLOAD_FOLDER']}")
    except Exception as e:
        app.logger.error(f"Failed to create upload folder: {e}")
    
    # Register blueprints
    try:
        from app.routes import auth, sites, inspections, uploads, reports, sync, settings
        
        app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
        app.register_blueprint(sites.bp, url_prefix='/api/v1/sites')
        app.register_blueprint(inspections.bp, url_prefix='/api/v1/inspections')
        app.register_blueprint(uploads.bp, url_prefix='/api/v1/upload')
        app.register_blueprint(reports.bp, url_prefix='/api/v1/reports')
        app.register_blueprint(sync.bp, url_prefix='/api/v1/sync')
        app.register_blueprint(settings.bp, url_prefix='/api/v1/settings')
        
        app.logger.info("All blueprints registered successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to register blueprints: {e}")
    
    # Health check endpoint
    @app.route('/health')
    def health():
        db_status = 'unknown'
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)[:100]}'
            app.logger.error(f"Database health check failed: {e}")
        
        return {
            'status': 'healthy' if db_status == 'connected' else 'degraded',
            'message': 'SolarSnap API is running',
            'database': db_status,
            'environment': config_name,
            'python_version': os.sys.version.split()[0]
        }, 200 if db_status == 'connected' else 503
    
    # Static images endpoint
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        from flask import send_from_directory
        try:
            return send_from_directory(os.path.join(app.root_path, 'static', 'images'), filename)
        except Exception as e:
            app.logger.error(f"Failed to serve image {filename}: {e}")
            return {'error': 'Image not found'}, 404
    
    # Root endpoint
    @app.route('/')
    def index():
        return {
            'message': 'SolarSnap API',
            'version': '1.0.0',
            'environment': config_name,
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'auth': '/api/v1/auth',
                'sites': '/api/v1/sites',
                'inspections': '/api/v1/inspections',
                'uploads': '/api/v1/upload',
                'reports': '/api/v1/reports',
                'sync': '/api/v1/sync',
                'settings': '/api/v1/settings'
            }
        }, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except:
            pass
        app.logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {e}")
        return {'error': 'An unexpected error occurred'}, 500
    
    return app
