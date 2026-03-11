#!/usr/bin/env python3
"""
Database migration script to update schema for production
Adds missing fields and updates existing data
"""
import os
from app import create_app, db
from sqlalchemy import text

def migrate_database():
    """Apply database migrations"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database migration...")
        
        try:
            # Test connection
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Add company_id to sites table if it doesn't exist
            try:
                db.session.execute(text("ALTER TABLE sites ADD COLUMN company_id VARCHAR(50)"))
                print("✅ Added company_id column to sites table")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ company_id column already exists in sites table")
                else:
                    print(f"⚠️ Could not add company_id to sites: {e}")
            
            # Add updated_at to sites table if it doesn't exist
            try:
                db.session.execute(text("ALTER TABLE sites ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                print("✅ Added updated_at column to sites table")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ updated_at column already exists in sites table")
                else:
                    print(f"⚠️ Could not add updated_at to sites: {e}")
            
            # Rename last_inspection to last_inspection_date in panels table
            try:
                db.session.execute(text("ALTER TABLE panels RENAME COLUMN last_inspection TO last_inspection_date"))
                print("✅ Renamed last_inspection to last_inspection_date in panels table")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print("ℹ️ last_inspection column doesn't exist, checking for last_inspection_date")
                    # Check if last_inspection_date already exists
                    try:
                        result = db.session.execute(text("SELECT last_inspection_date FROM panels LIMIT 1"))
                        print("ℹ️ last_inspection_date column already exists")
                    except:
                        print("⚠️ Neither last_inspection nor last_inspection_date exists")
                else:
                    print(f"⚠️ Could not rename column: {e}")
            
            # Add created_at and updated_at to panels table if they don't exist
            try:
                db.session.execute(text("ALTER TABLE panels ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                print("✅ Added created_at column to panels table")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ created_at column already exists in panels table")
                else:
                    print(f"⚠️ Could not add created_at to panels: {e}")
            
            try:
                db.session.execute(text("ALTER TABLE panels ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                print("✅ Added updated_at column to panels table")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️ updated_at column already exists in panels table")
                else:
                    print(f"⚠️ Could not add updated_at to panels: {e}")
            
            # Update existing sites to have company_id if they don't
            try:
                result = db.session.execute(text("UPDATE sites SET company_id = 'SOLARTECH-001' WHERE company_id IS NULL"))
                if result.rowcount > 0:
                    print(f"✅ Updated {result.rowcount} sites with default company_id")
                else:
                    print("ℹ️ All sites already have company_id set")
            except Exception as e:
                print(f"⚠️ Could not update sites company_id: {e}")
            
            # Update panel status values to lowercase
            try:
                status_updates = [
                    ("NOT_INSPECTED", "not_inspected"),
                    ("HEALTHY", "healthy"),
                    ("WARNING", "warning"),
                    ("CRITICAL", "critical")
                ]
                
                total_updated = 0
                for old_status, new_status in status_updates:
                    result = db.session.execute(text(f"UPDATE panels SET status = '{new_status}' WHERE status = '{old_status}'"))
                    total_updated += result.rowcount
                
                if total_updated > 0:
                    print(f"✅ Updated {total_updated} panel status values to lowercase")
                else:
                    print("ℹ️ Panel status values already correct")
                    
            except Exception as e:
                print(f"⚠️ Could not update panel status values: {e}")
            
            # Update inspection severity values to lowercase
            try:
                severity_updates = [
                    ("HEALTHY", "healthy"),
                    ("WARNING", "warning"),
                    ("CRITICAL", "critical")
                ]
                
                total_updated = 0
                for old_severity, new_severity in severity_updates:
                    result = db.session.execute(text(f"UPDATE inspections SET severity = '{new_severity}' WHERE severity = '{old_severity}'"))
                    total_updated += result.rowcount
                
                if total_updated > 0:
                    print(f"✅ Updated {total_updated} inspection severity values to lowercase")
                else:
                    print("ℹ️ Inspection severity values already correct")
                    
            except Exception as e:
                print(f"⚠️ Could not update inspection severity values: {e}")
            
            # Commit all changes
            db.session.commit()
            print("✅ All migrations committed successfully")
            
            # Verify the changes
            print("\n🔍 Verifying migration results...")
            
            # Check sites
            sites_count = db.session.execute(text("SELECT COUNT(*) FROM sites")).scalar()
            print(f"  Sites in database: {sites_count}")
            
            # Check panels
            panels_count = db.session.execute(text("SELECT COUNT(*) FROM panels")).scalar()
            print(f"  Panels in database: {panels_count}")
            
            # Check inspections
            inspections_count = db.session.execute(text("SELECT COUNT(*) FROM inspections")).scalar()
            print(f"  Inspections in database: {inspections_count}")
            
            print("\n🎉 Database migration completed successfully!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == '__main__':
    success = migrate_database()
    if not success:
        exit(1)