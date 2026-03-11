#!/usr/bin/env python3
"""
Render deployment script - runs automatically during build
Initializes database if needed, safe to run multiple times
"""
import os
import sys
import time

def post_deploy():
    """Post-deployment tasks"""
    print("🚀 SolarSnap Backend - Automatic Deployment Setup")
    print("=" * 60)
    
    # Wait a moment for database to be ready
    print("⏳ Waiting for database to be ready...")
    time.sleep(5)
    
    try:
        from app import create_app, db
        from app.models import User, Site, Panel, Inspection
        
        app = create_app()
        
        with app.app_context():
            # Test database connection with retries
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    db.session.execute('SELECT 1')
                    print("✅ Database connection successful")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⏳ Database connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(3)
                    else:
                        raise e
            
            # Check if database is already initialized
            try:
                user_count = User.query.count()
                site_count = Site.query.count()
                
                if user_count > 0 and site_count > 0:
                    print(f"ℹ️ Database already initialized:")
                    print(f"   👥 Users: {user_count}")
                    print(f"   🏭 Sites: {site_count}")
                    print(f"   ⚡ Panels: {Panel.query.count()}")
                    print(f"   📋 Inspections: {Inspection.query.count()}")
                    print("✅ Skipping initialization - database ready!")
                    return True
                    
            except Exception as e:
                print(f"ℹ️ Database tables don't exist yet: {e}")
            
            print("📊 Database is empty or incomplete, initializing...")
            
            # Create tables
            print("🔧 Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            # Import and run initialization
            print("🌱 Seeding database with sample data...")
            from init_db import seed_data
            
            seed_data()
            
            # Verify initialization
            final_user_count = User.query.count()
            final_site_count = Site.query.count()
            final_panel_count = Panel.query.count()
            final_inspection_count = Inspection.query.count()
            
            print("✅ Database initialization completed!")
            print(f"   👥 Users created: {final_user_count}")
            print(f"   🏭 Sites created: {final_site_count}")
            print(f"   ⚡ Panels created: {final_panel_count}")
            print(f"   📋 Inspections created: {final_inspection_count}")
            
            print("\n🔑 Test Credentials:")
            print("   📧 Email: inspector1@solartech.com")
            print("   🔒 Password: password123")
            print("   🏢 Company ID: SOLARTECH-001")
            
            print("\n🎉 SolarSnap Backend is ready for production!")
            return True
            
    except Exception as e:
        print(f"❌ Deployment setup failed: {e}")
        print("⚠️ The application will still start, but database may be empty")
        print("💡 You can manually run 'python init_db.py' later")
        # Don't fail the deployment, just warn
        return True

if __name__ == '__main__':
    success = post_deploy()
    # Always exit successfully so deployment doesn't fail
    sys.exit(0)