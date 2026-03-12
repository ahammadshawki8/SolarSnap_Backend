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

@bp.route('/add-sites', methods=['GET', 'POST'])
def add_demo_sites():
    """Add demo sites (small batch)"""
    try:
        # Check if sites already exist
        existing_sites = Site.query.count()
        if existing_sites > 0:
            return jsonify({
                'status': 'already_exists',
                'message': f'{existing_sites} sites already exist'
            }), 200
        
        # Create 3 demo sites
        sites = [
            Site(
                site_id='NV-SOLAR-01',
                site_name='Nevada Solar Farm 01',
                company_id='SOLARTECH-001',
                total_panels=50,  # Small number
                rows=5,
                panels_per_row=10,
                latitude=36.1234,
                longitude=-115.2345,
                status='active'
            ),
            Site(
                site_id='CA-SOLAR-01',
                site_name='California Solar Farm 01',
                company_id='SOLARTECH-001',
                total_panels=40,
                rows=4,
                panels_per_row=10,
                latitude=34.0522,
                longitude=-118.2437,
                status='active'
            ),
            Site(
                site_id='TX-SOLAR-01',
                site_name='Texas Solar Farm 01',
                company_id='SOLARTECH-001',
                total_panels=30,
                rows=3,
                panels_per_row=10,
                latitude=31.9686,
                longitude=-99.9018,
                status='active'
            )
        ]
        
        for site in sites:
            db.session.add(site)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Demo sites created',
            'sites_created': len(sites),
            'total_panels_planned': sum(s.total_panels for s in sites)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/add-panels/<site_id>', methods=['GET', 'POST'])
def add_demo_panels(site_id):
    """Add demo panels for a specific site"""
    try:
        # Get the site
        site = Site.query.get(site_id)
        if not site:
            return jsonify({'status': 'error', 'message': 'Site not found'}), 404
        
        # Check if panels already exist for this site
        existing_panels = Panel.query.filter_by(site_id=site_id).count()
        if existing_panels > 0:
            return jsonify({
                'status': 'already_exists',
                'message': f'{existing_panels} panels already exist for {site_id}'
            }), 200
        
        # Create panels for this site
        panels = []
        for row in range(1, site.rows + 1):
            for col in range(1, site.panels_per_row + 1):
                panel_num = (row - 1) * site.panels_per_row + col
                panel = Panel(
                    panel_id=f'PNL-{site_id}-{panel_num:03d}',
                    site_id=site_id,
                    row_number=row,
                    column_number=col,
                    string_number=(col - 1) // 5 + 1,
                    status='healthy'
                )
                panels.append(panel)
        
        # Add in batches of 20 to avoid memory issues
        for i in range(0, len(panels), 20):
            batch = panels[i:i+20]
            for panel in batch:
                db.session.add(panel)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Panels created for {site_id}',
            'panels_created': len(panels),
            'site_name': site.site_name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/add-inspections/<site_id>', methods=['GET', 'POST'])
def add_demo_inspections(site_id):
    """Add demo inspections for a site"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Get site and user
        site = Site.query.get(site_id)
        user = User.query.filter_by(email='inspector1@solartech.com').first()
        
        if not site or not user:
            return jsonify({'status': 'error', 'message': 'Site or user not found'}), 404
        
        # Check existing inspections
        existing_inspections = Inspection.query.filter_by(site_id=site_id).count()
        if existing_inspections > 0:
            return jsonify({
                'status': 'already_exists',
                'message': f'{existing_inspections} inspections already exist for {site_id}'
            }), 200
        
        # Get some panels from this site
        panels = Panel.query.filter_by(site_id=site_id).limit(15).all()
        
        if not panels:
            return jsonify({'status': 'error', 'message': 'No panels found for this site'}), 404
        
        # Create sample inspections
        inspections = []
        issue_types = ['none', 'hotspot', 'cell_crack', 'connection_fault', 'shading']
        
        for i, panel in enumerate(panels):
            # Generate realistic data
            ambient_temp = random.uniform(25, 35)
            panel_temp = ambient_temp + random.uniform(5, 25)
            delta_temp = random.uniform(0, 15)
            
            # Determine severity
            if delta_temp > 10:
                severity = 'critical'
                issue = random.choice(['hotspot', 'connection_fault'])
            elif delta_temp > 5:
                severity = 'warning'
                issue = random.choice(['cell_crack', 'shading'])
            else:
                severity = 'healthy'
                issue = 'none'
            
            inspection = Inspection(
                site_id=site_id,
                panel_id=panel.panel_id,
                inspector_id=user.user_id,
                temperature=panel_temp,
                delta_temp=delta_temp,
                severity=severity,
                issue_type=issue,
                latitude=site.latitude + random.uniform(-0.001, 0.001),
                longitude=site.longitude + random.uniform(-0.001, 0.001),
                thermal_image_url=f'/images/thermal/demo_{i+1:03d}.jpg',
                visual_image_url=f'/images/visual/demo_{i+1:03d}.jpg',
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                metadata={
                    'camera_model': 'FLIR ACE',
                    'ambient_temperature': ambient_temp,
                    'weather': 'clear'
                }
            )
            inspections.append(inspection)
        
        # Add inspections
        for inspection in inspections:
            db.session.add(inspection)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Demo inspections created for {site_id}',
            'inspections_created': len(inspections),
            'site_name': site.site_name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/demo-setup', methods=['GET', 'POST'])
def complete_demo_setup():
    """Complete demo setup guide"""
    try:
        # Check current state
        users = User.query.count()
        sites = Site.query.count()
        panels = Panel.query.count()
        inspections = Inspection.query.count()
        
        setup_steps = []
        
        if users == 0:
            setup_steps.append("1. Run /admin/minimal-init first")
        else:
            setup_steps.append("✅ Users ready")
        
        if sites == 0:
            setup_steps.append("2. Run /admin/add-sites")
        else:
            setup_steps.append("✅ Sites ready")
        
        if panels == 0 and sites > 0:
            site_list = [s.site_id for s in Site.query.all()]
            setup_steps.append(f"3. Run /admin/add-panels/<site_id> for: {', '.join(site_list)}")
        else:
            setup_steps.append("✅ Panels ready")
        
        if inspections == 0 and panels > 0:
            site_list = [s.site_id for s in Site.query.all()]
            setup_steps.append(f"4. Run /admin/add-inspections/<site_id> for: {', '.join(site_list)}")
        else:
            setup_steps.append("✅ Inspections ready")
        
        return jsonify({
            'status': 'info',
            'message': 'Demo setup guide',
            'current_counts': {
                'users': users,
                'sites': sites,
                'panels': panels,
                'inspections': inspections
            },
            'setup_steps': setup_steps,
            'available_endpoints': [
                '/admin/minimal-init',
                '/admin/add-sites',
                '/admin/add-panels/<site_id>',
                '/admin/add-inspections/<site_id>',
                '/admin/demo-setup (this guide)'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@bp.route('/fix-site-ids', methods=['GET', 'POST'])
def fix_site_ids():
    """Update site IDs to match what the Android app expects"""
    try:
        # Get current sites
        current_sites = Site.query.all()
        
        # Mapping of current IDs to expected IDs
        id_mapping = {
            'NV-SOLAR-01': 'NV-Solar-04',
            'CA-SOLAR-01': 'CA-Solar-01', 
            'TX-SOLAR-01': 'NV-Solar-03'  # Map Texas to the third expected site
        }
        
        updated_sites = []
        
        for site in current_sites:
            if site.site_id in id_mapping:
                new_id = id_mapping[site.site_id]
                old_id = site.site_id
                
                # Update panels first (foreign key constraint)
                panels = Panel.query.filter_by(site_id=old_id).all()
                for panel in panels:
                    # Update panel site_id
                    panel.site_id = new_id
                    # Update panel_id to match new site
                    panel.panel_id = panel.panel_id.replace(old_id, new_id)
                
                # Update inspections
                inspections = Inspection.query.filter_by(site_id=old_id).all()
                for inspection in inspections:
                    inspection.site_id = new_id
                    # Update panel_id reference in inspections
                    if inspection.panel_id:
                        inspection.panel_id = inspection.panel_id.replace(old_id, new_id)
                
                # Update site ID
                site.site_id = new_id
                
                updated_sites.append(f"{old_id} → {new_id}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Site IDs updated to match Android app expectations',
            'updates': updated_sites,
            'expected_sites': list(id_mapping.values())
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500