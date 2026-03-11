from app import db
from datetime import datetime

class Panel(db.Model):
    __tablename__ = 'panels'
    
    panel_id = db.Column(db.String(50), primary_key=True)
    site_id = db.Column(db.String(50), db.ForeignKey('sites.site_id'), nullable=False, index=True)
    row_number = db.Column(db.Integer)
    column_number = db.Column(db.Integer)
    string_number = db.Column(db.Integer)
    status = db.Column(db.String(50), default='not_inspected')
    last_inspection_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inspections = db.relationship('Inspection', backref='panel', lazy='dynamic')
    
    def get_latest_inspection(self):
        """Get the most recent inspection for this panel"""
        return self.inspections.order_by(db.desc('timestamp')).first()
    
    def to_dict(self):
        """Convert panel to dictionary"""
        latest = self.get_latest_inspection()
        
        data = {
            'panelId': self.panel_id,
            'siteId': self.site_id,
            'row': self.row_number,
            'column': self.column_number,
            'stringNumber': self.string_number,
            'status': self.status,
            'lastInspectionDate': self.last_inspection_date.isoformat() if self.last_inspection_date else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if latest:
            data['deltaTemp'] = latest.delta_temp
            data['issueType'] = latest.issue_type
            data['temperature'] = latest.temperature
            data['severity'] = latest.severity
        
        return data
    
    def __repr__(self):
        return f'<Panel {self.panel_id}>'
