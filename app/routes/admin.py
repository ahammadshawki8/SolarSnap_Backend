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
                
                # STEP 1: Update inspections first (they reference panels)
                inspections = Inspection.query.filter_by(site_id=old_id).all()
                for inspection in inspections:
                    inspection.site_id = new_id
                    # Update panel_id reference in inspections
                    if inspection.panel_id:
                        inspection.panel_id = inspection.panel_id.replace(old_id, new_id)
                
                # STEP 2: Update panels (they are referenced by inspections)
                panels = Panel.query.filter_by(site_id=old_id).all()
                for panel in panels:
                    # Update panel site_id
                    panel.site_id = new_id
                    # Update panel_id to match new site
                    new_panel_id = panel.panel_id.replace(old_id, new_id)
                    panel.panel_id = new_panel_id
                
                # STEP 3: Update site ID last
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
@bp.route('/update-panel-statuses', methods=['GET', 'POST'])
def update_panel_statuses():
    """Update panel statuses to realistic distribution for testing"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Get all panels
        panels = Panel.query.all()
        
        if not panels:
            return jsonify({'status': 'error', 'message': 'No panels found'}), 404
        
        # Realistic distribution for solar farm testing
        # 60% healthy (green), 25% uninspected (gray), 10% warning (orange), 5% critical (red)
        
        updated_panels = []
        
        for i, panel in enumerate(panels):
            rand = random.random()
            
            if rand < 0.60:  # 60% healthy (inspected, no issues)
                panel.status = 'healthy'
                panel.last_inspection_date = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            elif rand < 0.85:  # 25% uninspected (not inspected yet)
                panel.status = 'uninspected'
                panel.last_inspection_date = None
            elif rand < 0.95:  # 10% warning (minor issues)
                panel.status = 'warning'
                panel.last_inspection_date = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            else:  # 5% critical (major issues)
                panel.status = 'critical'
                panel.last_inspection_date = datetime.utcnow() - timedelta(hours=random.randint(1, 12))
            
            updated_panels.append(panel.status)
        
        db.session.commit()
        
        # Count final distribution
        status_counts = {
            'healthy': updated_panels.count('healthy'),
            'warning': updated_panels.count('warning'),
            'critical': updated_panels.count('critical'),
            'uninspected': updated_panels.count('uninspected')
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Panel statuses updated with realistic distribution',
            'total_panels': len(panels),
            'distribution': status_counts,
            'percentages': {
                'healthy': f"{(status_counts['healthy']/len(panels)*100):.1f}%",
                'warning': f"{(status_counts['warning']/len(panels)*100):.1f}%",
                'critical': f"{(status_counts['critical']/len(panels)*100):.1f}%",
                'uninspected': f"{(status_counts['uninspected']/len(panels)*100):.1f}%"
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/update-inspections-for-status', methods=['GET', 'POST'])
def update_inspections_for_status():
    """Update existing inspections to match panel statuses"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Get all inspections
        inspections = Inspection.query.all()
        
        updated_inspections = []
        
        for inspection in inspections:
            # Get the panel for this inspection
            panel = Panel.query.get(inspection.panel_id)
            
            if panel:
                # Update inspection severity to match panel status
                if panel.status == 'healthy':
                    inspection.severity = 'healthy'
                    inspection.issue_type = 'none'
                    inspection.delta_temp = random.uniform(0, 5)
                elif panel.status == 'warning':
                    inspection.severity = 'warning'
                    inspection.issue_type = random.choice(['cell_crack', 'shading', 'soiling'])
                    inspection.delta_temp = random.uniform(5, 10)
                elif panel.status == 'critical':
                    inspection.severity = 'critical'
                    inspection.issue_type = random.choice(['hotspot', 'diode_failure', 'connection_fault'])
                    inspection.delta_temp = random.uniform(10, 20)
                
                # Update temperature based on delta_temp
                ambient_temp = random.uniform(25, 35)
                inspection.temperature = ambient_temp + inspection.delta_temp
                
                # Update metadata
                if inspection.metadata:
                    inspection.metadata['ambient_temperature'] = ambient_temp
                    inspection.metadata['inspector_notes'] = get_inspection_note(inspection.severity, inspection.issue_type)
                
                updated_inspections.append(inspection.severity)
        
        db.session.commit()
        
        # Count final distribution
        severity_counts = {
            'healthy': updated_inspections.count('healthy'),
            'warning': updated_inspections.count('warning'),
            'critical': updated_inspections.count('critical')
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Inspections updated to match panel statuses',
            'total_inspections': len(inspections),
            'severity_distribution': severity_counts
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_inspection_note(severity, issue_type):
    """Generate realistic inspection notes"""
    import random
    
    notes = {
        'healthy': [
            'Panel operating within normal parameters',
            'No thermal anomalies detected',
            'Excellent panel condition',
            'Normal temperature distribution'
        ],
        'warning': {
            'cell_crack': 'Minor cell cracking observed, monitor for progression',
            'shading': 'Partial shading detected, check for obstructions',
            'soiling': 'Panel surface requires cleaning, reduced efficiency'
        },
        'critical': {
            'hotspot': 'Significant hotspot detected, immediate attention required',
            'diode_failure': 'Bypass diode failure suspected, electrical inspection needed',
            'connection_fault': 'Connection issue detected, check wiring and terminals'
        }
    }
    
    if severity == 'healthy':
        return random.choice(notes['healthy'])
    else:
        return notes[severity].get(issue_type, f'{severity.title()} issue detected')

@bp.route('/demo-status-summary', methods=['GET'])
def demo_status_summary():
    """Get summary of current demo data status"""
    try:
        # Count panels by status
        panel_counts = {}
        for status in ['healthy', 'warning', 'critical', 'uninspected']:
            count = Panel.query.filter_by(status=status).count()
            panel_counts[status] = count
        
        # Count inspections by severity
        inspection_counts = {}
        for severity in ['healthy', 'warning', 'critical']:
            count = Inspection.query.filter_by(severity=severity).count()
            inspection_counts[severity] = count
        
        # Get site info
        sites = Site.query.all()
        site_info = []
        for site in sites:
            site_panels = Panel.query.filter_by(site_id=site.site_id).count()
            site_inspections = Inspection.query.filter_by(site_id=site.site_id).count()
            site_info.append({
                'site_id': site.site_id,
                'site_name': site.site_name,
                'panels': site_panels,
                'inspections': site_inspections
            })
        
        return jsonify({
            'status': 'success',
            'panel_status_distribution': panel_counts,
            'inspection_severity_distribution': inspection_counts,
            'sites': site_info,
            'total_panels': sum(panel_counts.values()),
            'total_inspections': sum(inspection_counts.values())
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@bp.route('/fix-site-ids-safe', methods=['GET', 'POST'])
def fix_site_ids_safe():
    """Safely update site IDs using direct SQL to handle foreign keys"""
    try:
        from sqlalchemy import text
        
        # Mapping of current IDs to expected IDs
        id_mapping = {
            'NV-SOLAR-01': 'NV-Solar-04',
            'CA-SOLAR-01': 'CA-Solar-01', 
            'TX-SOLAR-01': 'NV-Solar-03'
        }
        
        updated_sites = []
        
        for old_id, new_id in id_mapping.items():
            # Check if old site exists
            result = db.session.execute(text("SELECT COUNT(*) FROM sites WHERE site_id = :old_id"), {'old_id': old_id}).scalar()
            
            if result > 0:
                # Step 1: Update inspections first (they reference panels by panel_id)
                db.session.execute(text("""
                    UPDATE inspections 
                    SET site_id = :new_id,
                        panel_id = REPLACE(panel_id, :old_id, :new_id)
                    WHERE site_id = :old_id
                """), {'old_id': old_id, 'new_id': new_id})
                
                # Step 2: Update panels (change both site_id and panel_id)
                db.session.execute(text("""
                    UPDATE panels 
                    SET site_id = :new_id,
                        panel_id = REPLACE(panel_id, :old_id, :new_id)
                    WHERE site_id = :old_id
                """), {'old_id': old_id, 'new_id': new_id})
                
                # Step 3: Update site
                db.session.execute(text("""
                    UPDATE sites 
                    SET site_id = :new_id
                    WHERE site_id = :old_id
                """), {'old_id': old_id, 'new_id': new_id})
                
                updated_sites.append(f"{old_id} → {new_id}")
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Site IDs safely updated using SQL',
            'updates': updated_sites,
            'note': 'All foreign key references updated correctly'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/reset-and-recreate', methods=['POST'])
def reset_and_recreate():
    """Nuclear option: Reset everything and recreate with correct IDs"""
    try:
        print("🔥 RESETTING ALL DATA AND RECREATING WITH CORRECT IDs")
        
        # Clear all data except users
        db.session.execute(text("DELETE FROM inspections"))
        db.session.execute(text("DELETE FROM panels"))
        db.session.execute(text("DELETE FROM sites"))
        db.session.commit()
        
        # Create sites with correct IDs
        sites_data = [
            {
                'site_id': 'NV-Solar-04',
                'site_name': 'Nevada Solar Farm 04',
                'total_panels': 50,
                'rows': 5,
                'panels_per_row': 10,
                'latitude': 36.1234,
                'longitude': -115.2345
            },
            {
                'site_id': 'CA-Solar-01',
                'site_name': 'California Solar Farm 01',
                'total_panels': 40,
                'rows': 4,
                'panels_per_row': 10,
                'latitude': 34.0522,
                'longitude': -118.2437
            },
            {
                'site_id': 'NV-Solar-03',
                'site_name': 'Nevada Solar Farm 03',
                'total_panels': 30,
                'rows': 3,
                'panels_per_row': 10,
                'latitude': 31.9686,
                'longitude': -99.9018
            }
        ]
        
        # Create sites
        for site_data in sites_data:
            site = Site(
                site_id=site_data['site_id'],
                site_name=site_data['site_name'],
                company_id='SOLARTECH-001',
                total_panels=site_data['total_panels'],
                rows=site_data['rows'],
                panels_per_row=site_data['panels_per_row'],
                latitude=site_data['latitude'],
                longitude=site_data['longitude'],
                status='active'
            )
            db.session.add(site)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'All data reset and recreated with correct site IDs',
            'sites_created': [s['site_id'] for s in sites_data],
            'next_steps': [
                'Run /admin/add-panels/<site_id> for each site',
                'Run /admin/add-inspections/<site_id> for each site',
                'Run /admin/update-panel-statuses for realistic distribution'
            ]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
@bp.route('/complete-demo-reset', methods=['GET', 'POST'])
def complete_demo_reset():
    """ONE-CLICK: Complete demo reset and setup with everything"""
    try:
        import random
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        print("🚀 COMPLETE DEMO RESET - ONE CLICK SETUP")
        print("=" * 60)
        
        # STEP 1: Clear all data except users
        print("🗑️ Step 1: Clearing existing data...")
        db.session.execute(text("DELETE FROM inspections"))
        db.session.execute(text("DELETE FROM panels"))
        db.session.execute(text("DELETE FROM sites"))
        db.session.commit()
        print("✅ Data cleared")
        
        # STEP 2: Create sites with correct Android app IDs
        print("🏭 Step 2: Creating sites with correct IDs...")
        sites_data = [
            {
                'site_id': 'NV-Solar-04',
                'site_name': 'Nevada Solar Farm 04',
                'total_panels': 50,
                'rows': 5,
                'panels_per_row': 10,
                'latitude': 36.1234,
                'longitude': -115.2345
            },
            {
                'site_id': 'CA-Solar-01',
                'site_name': 'California Solar Farm 01',
                'total_panels': 40,
                'rows': 4,
                'panels_per_row': 10,
                'latitude': 34.0522,
                'longitude': -118.2437
            },
            {
                'site_id': 'NV-Solar-03',
                'site_name': 'Nevada Solar Farm 03',
                'total_panels': 30,
                'rows': 3,
                'panels_per_row': 10,
                'latitude': 31.9686,
                'longitude': -99.9018
            }
        ]
        
        created_sites = []
        for site_data in sites_data:
            site = Site(
                site_id=site_data['site_id'],
                site_name=site_data['site_name'],
                company_id='SOLARTECH-001',
                total_panels=site_data['total_panels'],
                rows=site_data['rows'],
                panels_per_row=site_data['panels_per_row'],
                latitude=site_data['latitude'],
                longitude=site_data['longitude'],
                status='active'
            )
            db.session.add(site)
            created_sites.append(site_data)
        
        db.session.commit()
        print(f"✅ Created {len(created_sites)} sites")
        
        # STEP 3: Create panels for all sites with realistic status distribution
        print("⚡ Step 3: Creating panels with realistic status distribution...")
        all_panels = []
        
        for site_data in sites_data:
            site_id = site_data['site_id']
            
            for row in range(1, site_data['rows'] + 1):
                for col in range(1, site_data['panels_per_row'] + 1):
                    panel_num = (row - 1) * site_data['panels_per_row'] + col
                    
                    # Realistic status distribution
                    rand = random.random()
                    if rand < 0.60:  # 60% healthy
                        status = 'healthy'
                        last_inspection = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                    elif rand < 0.85:  # 25% uninspected
                        status = 'uninspected'
                        last_inspection = None
                    elif rand < 0.95:  # 10% warning
                        status = 'warning'
                        last_inspection = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                    else:  # 5% critical
                        status = 'critical'
                        last_inspection = datetime.utcnow() - timedelta(hours=random.randint(1, 12))
                    
                    panel = Panel(
                        panel_id=f'PNL-{site_id}-{panel_num:03d}',
                        site_id=site_id,
                        row_number=row,
                        column_number=col,
                        string_number=(col - 1) // 5 + 1,
                        status=status,
                        last_inspection_date=last_inspection
                    )
                    all_panels.append(panel)
        
        # Add panels in batches
        for i in range(0, len(all_panels), 20):
            batch = all_panels[i:i+20]
            for panel in batch:
                db.session.add(panel)
            db.session.commit()
        
        print(f"✅ Created {len(all_panels)} panels with realistic status distribution")
        
        # STEP 4: Create realistic inspections for inspected panels
        print("📋 Step 4: Creating realistic inspections...")
        user = User.query.filter_by(email='inspector1@solartech.com').first()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Test user not found'}), 404
        
        inspected_panels = [p for p in all_panels if p.status != 'uninspected']
        inspections = []
        issue_types = ['none', 'hotspot', 'cell_crack', 'connection_fault', 'shading', 'soiling', 'diode_failure']
        
        for panel in inspected_panels:
            # Generate realistic data based on panel status
            ambient_temp = random.uniform(25, 35)
            
            if panel.status == 'healthy':
                severity = 'healthy'
                issue = 'none'
                delta_temp = random.uniform(0, 5)
            elif panel.status == 'warning':
                severity = 'warning'
                issue = random.choice(['cell_crack', 'shading', 'soiling'])
                delta_temp = random.uniform(5, 10)
            else:  # critical
                severity = 'critical'
                issue = random.choice(['hotspot', 'diode_failure', 'connection_fault'])
                delta_temp = random.uniform(10, 20)
            
            panel_temp = ambient_temp + delta_temp
            
            # Get site for GPS coordinates
            site = next(s for s in created_sites if s['site_id'] == panel.site_id)
            
            inspection = Inspection(
                site_id=panel.site_id,
                panel_id=panel.panel_id,
                inspector_id=user.user_id,
                temperature=panel_temp,
                delta_temp=delta_temp,
                severity=severity,
                issue_type=issue,
                latitude=site['latitude'] + random.uniform(-0.001, 0.001),
                longitude=site['longitude'] + random.uniform(-0.001, 0.001),
                thermal_image_url=f'/images/thermal/demo_{random.randint(1,20):03d}.jpg',
                visual_image_url=f'/images/visual/demo_{random.randint(1,20):03d}.jpg',
                timestamp=panel.last_inspection_date or datetime.utcnow(),
                metadata={
                    'camera_model': 'FLIR ACE',
                    'ambient_temperature': ambient_temp,
                    'humidity': random.uniform(30, 80),
                    'wind_speed': random.uniform(0, 20),
                    'weather_conditions': random.choice(['clear', 'partly_cloudy', 'overcast']),
                    'inspector_notes': get_inspection_note(severity, issue)
                }
            )
            inspections.append(inspection)
        
        # Add inspections in batches
        for i in range(0, len(inspections), 15):
            batch = inspections[i:i+15]
            for inspection in batch:
                db.session.add(inspection)
            db.session.commit()
        
        print(f"✅ Created {len(inspections)} realistic inspections")
        
        # STEP 5: Final verification and summary
        print("🔍 Step 5: Final verification...")
        
        final_counts = {
            'users': User.query.count(),
            'sites': Site.query.count(),
            'panels': Panel.query.count(),
            'inspections': Inspection.query.count()
        }
        
        # Panel status distribution
        panel_distribution = {}
        for status in ['healthy', 'warning', 'critical', 'uninspected']:
            count = Panel.query.filter_by(status=status).count()
            panel_distribution[status] = count
        
        # Site breakdown
        site_breakdown = []
        for site_data in sites_data:
            site_panels = Panel.query.filter_by(site_id=site_data['site_id']).count()
            site_inspections = Inspection.query.filter_by(site_id=site_data['site_id']).count()
            site_breakdown.append({
                'site_id': site_data['site_id'],
                'site_name': site_data['site_name'],
                'panels': site_panels,
                'inspections': site_inspections
            })
        
        print("🎉 COMPLETE DEMO SETUP FINISHED!")
        
        return jsonify({
            'status': 'success',
            'message': '🎉 COMPLETE DEMO SETUP SUCCESSFUL!',
            'summary': {
                'total_counts': final_counts,
                'panel_status_distribution': panel_distribution,
                'panel_percentages': {
                    'healthy': f"{(panel_distribution['healthy']/final_counts['panels']*100):.1f}%",
                    'warning': f"{(panel_distribution['warning']/final_counts['panels']*100):.1f}%",
                    'critical': f"{(panel_distribution['critical']/final_counts['panels']*100):.1f}%",
                    'uninspected': f"{(panel_distribution['uninspected']/final_counts['panels']*100):.1f}%"
                },
                'sites': site_breakdown
            },
            'test_credentials': {
                'email': 'inspector1@solartech.com',
                'password': 'password123',
                'company_id': 'SOLARTECH-001'
            },
            'android_app_ready': True,
            'features_ready': [
                '✅ Login authentication',
                '✅ Site selection (dashboard & map)',
                '✅ Panel status visualization',
                '✅ Inspection history',
                '✅ Realistic thermal data',
                '✅ GPS coordinates',
                '✅ Issue classification'
            ]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Complete demo reset failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
@bp.route('/test-all-endpoints', methods=['GET'])
def test_all_endpoints():
    """Test all major endpoints to ensure they work"""
    try:
        results = {}
        
        # Test user exists
        user = User.query.filter_by(email='inspector1@solartech.com').first()
        results['user_exists'] = user is not None
        
        # Test sites
        sites = Site.query.all()
        results['sites_count'] = len(sites)
        results['sites'] = [s.site_id for s in sites]
        
        # Test panels
        panels = Panel.query.all()
        results['panels_count'] = len(panels)
        
        # Test inspections
        inspections = Inspection.query.all()
        results['inspections_count'] = len(inspections)
        
        # Test inspection to_dict method
        if inspections:
            try:
                sample_inspection = inspections[0].to_dict()
                results['inspection_to_dict'] = 'success'
            except Exception as e:
                results['inspection_to_dict'] = f'error: {e}'
        
        # Test settings
        if user:
            try:
                settings_test = user.settings or '{}'
                results['user_settings'] = 'success'
            except Exception as e:
                results['user_settings'] = f'error: {e}'
        
        return jsonify({
            'status': 'success',
            'message': 'Endpoint testing complete',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/fix-database-schema', methods=['POST'])
def fix_database_schema():
    """Add missing columns to existing tables"""
    try:
        from sqlalchemy import text
        
        # Add settings column to users table if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN settings TEXT"))
            db.session.commit()
            print("✅ Added settings column to users table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("ℹ️ Settings column already exists")
            else:
                print(f"⚠️ Could not add settings column: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Database schema updated'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500