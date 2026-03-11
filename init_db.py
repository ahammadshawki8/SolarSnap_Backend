"""
Initialize database with tables and seed data
Run this script to set up the database for the first time
Works with both SQLite (development) and PostgreSQL (production)
"""
import os
from app import create_app, db
from app.models import User, Site, Panel, Inspection, UploadQueue
from datetime import datetime, timedelta
import random

def init_database():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Initializing SolarSnap Database...")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            print("✓ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        print("\nCreating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if data already exists
        if User.query.first():
            print("⚠ Database already contains data.")
            response = input("Do you want to reset and reseed the database? (y/N): ")
            if response.lower() == 'y':
                print("🗑️ Clearing existing data...")
                clear_data()
            else:
                print("Skipping seed data.")
                return True
        
        print("\n🌱 Seeding database with sample data...")
        seed_data()
        print("✅ Database initialization completed successfully!")
        return True

def clear_data():
    """Clear all existing data"""
    try:
        # Delete in reverse order of dependencies
        db.session.query(UploadQueue).delete()
        db.session.query(Inspection).delete()
        db.session.query(Panel).delete()
        db.session.query(Site).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("✓ Existing data cleared")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error clearing data: {e}")
        raise

def seed_data():
    """Add sample data for testing"""
    
    try:
        # Create test users
        print("  👥 Creating users...")
        users = []
        user_data = [
            {'email': 'inspector1@solartech.com', 'name': 'John Inspector', 'role': 'inspector'},
            {'email': 'manager1@solartech.com', 'name': 'Sarah Manager', 'role': 'manager'},
            {'email': 'admin1@solartech.com', 'name': 'Mike Admin', 'role': 'admin'}
        ]
        
        for user_info in user_data:
            user = User(
                email=user_info['email'],
                full_name=user_info['name'],
                role=user_info['role'],
                company_id='SOLARTECH-001',
                is_active=True
            )
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"    ✓ Created {len(users)} users")
        
        # Create test sites
        print("  🏭 Creating sites...")
        sites = [
            Site(
                site_id='NV-Solar-04',
                site_name='Nevada Solar Farm 04',
                company_id='SOLARTECH-001',
                total_panels=1200,
                rows=15,
                panels_per_row=80,
                latitude=36.1234,
                longitude=-115.2345,
                status='active'
            ),
            Site(
                site_id='NV-Solar-03',
                site_name='Nevada Solar Farm 03',
                company_id='SOLARTECH-001',
                total_panels=800,
                rows=10,
                panels_per_row=80,
                latitude=36.1456,
                longitude=-115.2567,
                status='active'
            ),
            Site(
                site_id='CA-Solar-01',
                site_name='California Solar Farm 01',
                company_id='SOLARTECH-001',
                total_panels=1500,
                rows=20,
                panels_per_row=75,
                latitude=34.0522,
                longitude=-118.2437,
                status='active'
            )
        ]
        
        for site in sites:
            db.session.add(site)
        
        db.session.commit()
        print(f"    ✓ Created {len(sites)} sites")
        
        # Create panels for all sites
        print("  ⚡ Creating panels...")
        create_panels_for_sites(sites)
        
        # Create sample inspections
        print("  📋 Creating sample inspections...")
        create_sample_inspections(users, sites)
        
        # Create sample upload queue entries
        print("  📤 Creating upload queue entries...")
        create_upload_queue_entries()
        
        print("\n✅ All seed data created successfully!")
        print_test_credentials()
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding data: {e}")
        raise

def create_panels_for_sites(sites):
    """Create panels for all sites with realistic status distribution"""
    all_panels = []
    
    for site in sites:
        site_panels = []
        prefix = site.site_id.replace('-', '')[:4].upper()
        
        for row in range(1, site.rows + 1):
            for col in range(1, site.panels_per_row + 1):
                panel_id = f"PNL-{prefix}-{(row-1)*site.panels_per_row + col:04d}"
                
                # Realistic status distribution
                rand = random.random()
                if rand < 0.65:  # 65% healthy
                    status = 'healthy'
                elif rand < 0.85:  # 20% warning
                    status = 'warning'
                elif rand < 0.95:  # 10% critical
                    status = 'critical'
                else:  # 5% not inspected
                    status = 'not_inspected'
                
                panel = Panel(
                    panel_id=panel_id,
                    site_id=site.site_id,
                    row_number=row,
                    column_number=col,
                    string_number=(col - 1) // 10 + 1,
                    status=status,
                    last_inspection_date=datetime.utcnow() - timedelta(hours=random.randint(1, 168)) if status != 'not_inspected' else None
                )
                site_panels.append(panel)
        
        all_panels.extend(site_panels)
        print(f"    ✓ Created {len(site_panels)} panels for {site.site_name}")
    
    # Bulk insert for better performance
    db.session.bulk_save_objects(all_panels)
    db.session.commit()
    print(f"    ✓ Total panels created: {len(all_panels)}")

def create_sample_inspections(users, sites):
    """Create realistic sample inspections"""
    inspections = []
    issue_types = ['none', 'hotspot', 'diode_failure', 'cell_crack', 'connection_fault', 'shading', 'soiling']
    
    # Mock image URLs
    thermal_images = [f'/images/thermal/thermal_{i:03d}.jpg' for i in range(1, 11)]
    visual_images = [f'/images/visual/visual_{i:03d}.jpg' for i in range(1, 11)]
    
    inspection_counts = {'NV-Solar-04': 75, 'NV-Solar-03': 50, 'CA-Solar-01': 60}
    
    for site in sites:
        count = inspection_counts.get(site.site_id, 50)
        prefix = site.site_id.replace('-', '')[:4].upper()
        
        for i in range(count):
            panel_num = random.randint(1, min(500, site.total_panels))
            panel_id = f"PNL-{prefix}-{panel_num:04d}"
            
            # Generate realistic temperature data
            ambient_temp = random.uniform(25, 40)
            panel_temp = ambient_temp + random.uniform(5, 35)
            delta_temp = random.uniform(0, 25)
            
            # Determine severity and issue based on delta_temp
            if delta_temp > 15:
                severity = 'critical'
                issue = random.choice(['hotspot', 'diode_failure', 'connection_fault'])
            elif delta_temp > 8:
                severity = 'warning'
                issue = random.choice(['cell_crack', 'shading', 'soiling', 'hotspot'])
            else:
                severity = 'healthy'
                issue = 'none'
            
            inspection = Inspection(
                site_id=site.site_id,
                panel_id=panel_id,
                inspector_id=users[0].user_id,
                temperature=panel_temp,
                delta_temp=delta_temp,
                severity=severity,
                issue_type=issue,
                latitude=site.latitude + random.uniform(-0.002, 0.002),
                longitude=site.longitude + random.uniform(-0.002, 0.002),
                thermal_image_url=random.choice(thermal_images),
                visual_image_url=random.choice(visual_images),
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(0, 168)),
                metadata={
                    'camera_model': 'FLIR ACE',
                    'ambient_temperature': ambient_temp,
                    'humidity': random.uniform(30, 80),
                    'wind_speed': random.uniform(0, 20),
                    'inspection_duration': random.randint(30, 300),
                    'weather_conditions': random.choice(['clear', 'partly_cloudy', 'overcast']),
                    'inspector_notes': random.choice([
                        'Normal inspection, no issues detected',
                        'Slight temperature elevation observed',
                        'Panel requires cleaning',
                        'Minor shading from nearby vegetation',
                        'Excellent panel condition'
                    ])
                }
            )
            inspections.append(inspection)
    
    db.session.bulk_save_objects(inspections)
    db.session.commit()
    print(f"    ✓ Created {len(inspections)} inspections")

def create_upload_queue_entries():
    """Create sample upload queue entries"""
    queue_entries = []
    statuses = ['pending', 'uploading', 'completed', 'failed']
    
    # Get some recent inspections
    recent_inspections = Inspection.query.order_by(Inspection.created_at.desc()).limit(10).all()
    
    for i, inspection in enumerate(recent_inspections):
        status = random.choice(statuses)
        
        entry = UploadQueue(
            inspection_id=inspection.inspection_id,
            file_path=f'/uploads/thermal_{inspection.inspection_id}.jpg',
            file_size=random.randint(500000, 5000000),  # 500KB to 5MB
            status=status,
            retry_count=random.randint(0, 3) if status == 'failed' else 0,
            error_message='Network timeout' if status == 'failed' else None,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        )
        queue_entries.append(entry)
    
    db.session.bulk_save_objects(queue_entries)
    db.session.commit()
    print(f"    ✓ Created {len(queue_entries)} upload queue entries")

def print_test_credentials():
    """Print test credentials for easy access"""
    print("\n" + "="*50)
    print("🔑 TEST CREDENTIALS")
    print("="*50)
    print("Inspector Account:")
    print("  📧 Email: inspector1@solartech.com")
    print("  🔒 Password: password123")
    print("  🏢 Company ID: SOLARTECH-001")
    print()
    print("Manager Account:")
    print("  📧 Email: manager1@solartech.com")
    print("  🔒 Password: password123")
    print("  🏢 Company ID: SOLARTECH-001")
    print()
    print("Admin Account:")
    print("  📧 Email: admin1@solartech.com")
    print("  🔒 Password: password123")
    print("  🏢 Company ID: SOLARTECH-001")
    print("="*50)

if __name__ == '__main__':
    success = init_database()
    if not success:
        exit(1)
