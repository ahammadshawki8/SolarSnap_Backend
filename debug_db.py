#!/usr/bin/env python3
"""
Debug database issues - check what's actually happening
"""
import os
import sys

def debug_database():
    """Debug database state and issues"""
    print("🔍 DEBUGGING DATABASE STATE")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from sqlalchemy import text, inspect
        
        app = create_app()
        
        with app.app_context():
            print(f"Environment: {os.getenv('FLASK_ENV', 'unknown')}")
            print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Test basic connection
            print("\n🔍 Testing database connection...")
            try:
                result = db.session.execute(text('SELECT 1'))
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Check what tables exist
            print("\n🔍 Checking existing tables...")
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables: {existing_tables}")
            
            if not existing_tables:
                print("❌ NO TABLES EXIST - Database is empty!")
                return False
            
            # Try to import models
            print("\n🔍 Testing model imports...")
            try:
                from app.models import User, Site, Panel, Inspection, UploadQueue
                print("✅ All models imported successfully")
            except Exception as e:
                print(f"❌ Model import failed: {e}")
                return False
            
            # Check each table
            print("\n🔍 Checking table contents...")
            tables_to_check = [
                ('users', User),
                ('sites', Site), 
                ('panels', Panel),
                ('inspections', Inspection),
                ('upload_queue', UploadQueue)
            ]
            
            for table_name, model_class in tables_to_check:
                try:
                    count = model_class.query.count()
                    print(f"✅ {table_name}: {count} records")
                except Exception as e:
                    print(f"❌ {table_name}: ERROR - {e}")
            
            # Test specific login user
            print("\n🔍 Testing login user...")
            try:
                test_user = User.query.filter_by(email='inspector1@solartech.com').first()
                if test_user:
                    print("✅ Test user exists")
                    if test_user.check_password('password123'):
                        print("✅ Password verification works")
                    else:
                        print("❌ Password verification failed")
                else:
                    print("❌ Test user does not exist")
            except Exception as e:
                print(f"❌ User lookup failed: {e}")
            
            # Test JWT token creation
            print("\n🔍 Testing JWT token creation...")
            try:
                from flask_jwt_extended import create_access_token
                token = create_access_token(identity=1)
                print("✅ JWT token creation works")
            except Exception as e:
                print(f"❌ JWT token creation failed: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_database()