#!/usr/bin/env python3
"""
Production deployment script for SolarSnap Backend
Handles database initialization and production setup
"""
import os
import sys
from app import create_app, db
from app.models import User

def deploy():
    """Run deployment tasks"""
    print("🚀 Starting SolarSnap Backend deployment...")
    
    # Create app with production config
    app = create_app()
    
    with app.app_context():
        # Test database connection
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Create tables
        print("📊 Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(email='admin1@solartech.com').first()
        if not admin_user:
            print("👤 Creating admin user...")
            admin = User(
                email='admin1@solartech.com',
                full_name='System Administrator',
                role='admin',
                company_id='SOLARTECH-001',
                is_active=True
            )
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
        else:
            print("ℹ️ Admin user already exists")
        
        # Create upload directory
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        print(f"📁 Upload directory ready: {upload_dir}")
        
        print("🎉 Deployment completed successfully!")
        return True

if __name__ == '__main__':
    success = deploy()
    if not success:
        sys.exit(1)