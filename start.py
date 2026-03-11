#!/usr/bin/env python3
"""
Production startup script for Render deployment
Handles initialization and starts the application
"""
import os
import sys
from app import create_app, db

def startup():
    """Handle startup tasks"""
    print("🚀 SolarSnap Backend - Production Startup")
    
    # Create app
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            print("✅ Database connection successful")
            
            # Create tables if they don't exist
            db.create_all()
            print("✅ Database tables ready")
            
            # Create upload directory
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            print("✅ Upload directory ready")
            
            print("🎉 Startup completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Startup failed: {e}")
            return False

if __name__ == '__main__':
    success = startup()
    if not success:
        sys.exit(1)