from app import db
from datetime import datetime

class Site(db.Model):
    __tablename__ = 'sites'
    
    site_id = db.Column(db.String(50), primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)
    total_panels = db.Column(db.Integer, default=0)
    rows = db.Column(db.Integer, default=0)
    panels_per_row = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    panels = db.relationship('Panel', backref='site', lazy='dynamic', cascade='all, delete-orphan')
    inspections = db.relationship('Inspection', backref='site', lazy='dynamic')
    
    def get_statistics(self):
        """Calculate site statistics"""
        from app.models.inspection import Inspection
        
        # Get today's inspections
        today = datetime.utcnow().date()
        inspections_today = Inspection.query.filter(
            Inspection.site_id == self.site_id,
            db.func.date(Inspection.timestamp) == today
        ).all()
        
        critical = sum(1 for i in inspections_today if i.severity == 'CRITICAL')
        warnings = sum(1 for i in inspections_today if i.severity == 'WARNING')
        healthy = sum(1 for i in inspections_today if i.severity == 'HEALTHY')
        uninspected = self.total_panels - len(inspections_today)
        
        return {
            'criticalFaults': critical,
            'warnings': warnings,
            'healthyPanels': healthy,
            'uninspected': uninspected
        }
    
    def to_dict(self, include_stats=False):
        """Convert site to dictionary"""
        data = {
            'siteId': self.site_id,
            'siteName': self.site_name,
            'totalPanels': self.total_panels,
            'rows': self.rows,
            'panelsPerRow': self.panels_per_row,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status
        }
        
        if include_stats:
            data['statistics'] = self.get_statistics()
        
        return data
    
    def __repr__(self):
        return f'<Site {self.site_id}>'
