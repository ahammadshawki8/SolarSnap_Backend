from flask import Blueprint, jsonify
from app import db
from app.models import User, Site, Panel, Inspection, UploadQueue

bp = Blueprint('admin', __name__)

@bp.route('/init-db', methods=['GET', 'POST'])
def init_database():
    """Manual database initialization endpoint"""
    try:
        from sqlalchemy import text, inspect
        
        # Check if already initialized
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables and len(existing_tables) > 0:
            # Check if we have data
            try:
                user_count = User.query.count()
                if user_count > 0:
                    return jsonify({
                        'status': 'already_initialized',
                        'message': 'Database already has data',
                        'tables': existing_tables,
                        'user_count': user_count,
                        'test_credentials': {
                            'email': 'inspector1@solartech.com',
                            'password': 'password123',
                            'company_id': 'SOLARTECH-001'
                        }
                    }), 200
            except:
                pass
        
        # Force initialization
        print("🔥 Manual database initialization requested via endpoint")
        
        # Drop and recreate
        print("🗑️ Dropping all tables...")
        db.drop_all()
        
        print("🔧 Creating all tables...")
        db.create_all()
        
        # Import and run seed data
        print("🌱 Running seed data...")
        from init_db import seed_data
        seed_data()
        
        # Verify
        final_counts = {
            'users': User.query.count(),
            'sites': Site.query.count(),
            'panels': Panel.query.count(),
            'inspections': Inspection.query.count(),
            'upload_queue': UploadQueue.query.count()
        }
        
        print(f"✅ Manual initialization complete: {final_counts}")
        
        return jsonify({
            'status': 'success',
            'message': 'Database initialized successfully',
            'counts': final_counts,
            'test_credentials': {
                'email': 'inspector1@solartech.com',
                'password': 'password123',
                'company_id': 'SOLARTECH-001'
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Manual DB init failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@bp.route('/debug-db', methods=['GET'])
def debug_database():
    """Debug database state"""
    try:
        from sqlalchemy import text, inspect
        
        # Check connection
        db.session.execute(text('SELECT 1'))
        
        # Check tables
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Check counts
        counts = {}
        if existing_tables:
            try:
                counts['users'] = User.query.count()
                counts['sites'] = Site.query.count()
                counts['panels'] = Panel.query.count()
                counts['inspections'] = Inspection.query.count()
                counts['upload_queue'] = UploadQueue.query.count()
            except Exception as e:
                counts['error'] = str(e)
        
        # Test user
        test_user_exists = False
        try:
            test_user = User.query.filter_by(email='inspector1@solartech.com').first()
            test_user_exists = test_user is not None
        except:
            pass
        
        return jsonify({
            'status': 'success',
            'database_connected': True,
            'existing_tables': existing_tables,
            'table_counts': counts,
            'test_user_exists': test_user_exists
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/minimal-init', methods=['GET', 'POST'])
def minimal_init():
    """Ultra minimal - just create one user for login testing"""
    try:
        print("🚀 MINIMAL initialization - just one user")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email='inspector1@solartech.com').first()
        if existing_user:
            return jsonify({
                'status': 'already_exists',
                'message': 'Test user already exists',
                'user_email': existing_user.email,
                'can_login': True
            }), 200
        
        # Create ONLY the test user - nothing else
        user = User(
            email='inspector1@solartech.com',
            full_name='John Inspector',
            role='inspector',
            company_id='SOLARTECH-001'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        print("✅ Single user created successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Minimal user created - login should work now',
            'user_created': True,
            'test_credentials': {
                'email': 'inspector1@solartech.com',
                'password': 'password123',
                'company_id': 'SOLARTECH-001'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Minimal init failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/reset-db', methods=['POST'])
def reset_database():
    """Force reset database (POST only for safety)"""
    try:
        print("🔥 FORCE DATABASE RESET requested")
        
        # Drop everything
        db.drop_all()
        print("🗑️ All tables dropped")
        
        # Recreate
        db.create_all()
        print("🔧 All tables recreated")
        
        # Seed
        from init_db import seed_data
        seed_data()
        print("🌱 Seed data created")
        
        # Verify
        final_counts = {
            'users': User.query.count(),
            'sites': Site.query.count(),
            'panels': Panel.query.count(),
            'inspections': Inspection.query.count()
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Database reset and reinitialized',
            'counts': final_counts
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/test-login', methods=['GET', 'POST'])
def test_login():
    """Test login functionality with detailed debugging"""
    try:
        # Get the test user
        test_user = User.query.filter_by(email='inspector1@solartech.com').first()
        
        if not test_user:
            return jsonify({
                'status': 'error',
                'message': 'Test user not found',
                'all_users': [u.email for u in User.query.all()]
            }), 404
        
        # Test password verification
        password_test = test_user.check_password('password123')
        
        # Try creating JWT token
        try:
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=test_user.user_id)
            token_test = True
        except Exception as e:
            token_test = f"JWT Error: {e}"
        
        return jsonify({
            'status': 'success',
            'user_found': True,
            'user_email': test_user.email,
            'user_id': test_user.user_id,
            'company_id': test_user.company_id,
            'password_hash_exists': bool(test_user.password_hash),
            'password_verification': password_test,
            'jwt_token_creation': token_test,
            'user_dict': test_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': str(e)
        }), 500

@bp.route('/sql-init', methods=['GET', 'POST'])
def sql_init():
    """Direct SQL initialization - fastest possible"""
    try:
        from sqlalchemy import text
        import bcrypt
        
        print("🚀 Direct SQL initialization")
        
        # Check if user exists
        result = db.session.execute(text("SELECT COUNT(*) FROM users WHERE email = 'inspector1@solartech.com'")).scalar()
        
        if result > 0:
            return jsonify({
                'status': 'already_exists',
                'message': 'User already exists via SQL check'
            }), 200
        
        # Hash password
        password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Direct SQL insert - fastest possible
        db.session.execute(text("""
            INSERT INTO users (email, password_hash, full_name, role, company_id, created_at)
            VALUES ('inspector1@solartech.com', :password_hash, 'John Inspector', 'inspector', 'SOLARTECH-001', NOW())
        """), {'password_hash': password_hash})
        
        db.session.commit()
        
        print("✅ Direct SQL user creation successful")
        
        return jsonify({
            'status': 'success',
            'message': 'User created via direct SQL - login should work',
            'method': 'direct_sql',
            'test_credentials': {
                'email': 'inspector1@solartech.com',
                'password': 'password123',
                'company_id': 'SOLARTECH-001'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ SQL init failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500