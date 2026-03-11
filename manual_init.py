#!/usr/bin/env python3
"""
Manual database initialization script for production
Run this if automatic initialization failed
FORCES complete database reset and initialization
"""
import os
import sys

def manual_init():
    """Manually initialize database with FORCE RESET"""
    print("🔧 MANUAL FORCE DATABASE INITIALIZATION")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.models import User, Site, Panel, Inspection, UploadQueue
        from sqlalchemy import text
        
        app = create_app()
        
        with app.app_context():
            # Test connection
            print("🔍 Testing database connection...")
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # FORCE COMPLETE RESET
            print("🔥 FORCING COMPLETE DATABASE RESET...")
            
            # Drop all tables
            try:
                print("🗑️ Dropping all existing tables...")
                db.drop_all()
                print("✅ All tables dropped")
            except Exception as e:
                print(f"ℹ️ Drop failed (tables probably didn't exist): {e}")
            
            # Create all tables fresh
            print("🔧 Creating ALL database tables from scratch...")
            db.create_all()
            print("✅ All database tables created successfully")
            
            # Verify each table exists
            print("🔍 Verifying all tables...")
            tables = ['users', 'sites', 'panels', 'inspections', 'upload_queue']
            for table in tables:
                try:
                    db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    print(f"✅ {table} table verified")
                except Exception as e:
                    print(f"❌ {table} table verification failed: {e}")
                    raise e
            
            # FORCE SEED DATA
            print("🌱 FORCING complete seed data creation...")
            from init_db import seed_data
            seed_data()
            
            # Final verification with counts
            print("🔍 FINAL VERIFICATION WITH COUNTS...")
            final_user_count = User.query.count()
            final_site_count = Site.query.count()
            final_panel_count = Panel.query.count()
            final_inspection_count = Inspection.query.count()
            final_queue_count = UploadQueue.query.count()
            
            print(f"✅ MANUAL INITIALIZATION COMPLETE!")
            print(f"   👥 Users: {final_user_count}")
            print(f"   🏭 Sites: {final_site_count}")
            print(f"   ⚡ Panels: {final_panel_count}")
            print(f"   📋 Inspections: {final_inspection_count}")
            print(f"   📤 Upload Queue: {final_queue_count}")
            
            # Ensure we have data
            if final_user_count == 0 or final_site_count == 0:
                raise Exception("CRITICAL: No data was created!")
            
            # Test authentication
            print("\n🧪 Testing authentication...")
            test_user = User.query.filter_by(email='inspector1@solartech.com').first()
            if test_user and test_user.check_password('password123'):
                print("✅ Authentication test PASSED")
            else:
                raise Exception("Authentication test FAILED")
            
            print("\n🔑 CONFIRMED WORKING CREDENTIALS:")
            print("   📧 Email: inspector1@solartech.com")
            print("   🔒 Password: password123")
            print("   🏢 Company ID: SOLARTECH-001")
            
            print("\n🎉 DATABASE IS FULLY READY!")
            return True
            
    except Exception as e:
        print(f"❌ Manual initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = manual_init()
    sys.exit(0 if success else 1)