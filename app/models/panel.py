from app import db
from datetime import datetime

class Panel(db.Model):
    __tablename__ = 'panels'
    
    panel_id = db.Column(db.String(50), primary_key=True)
    site_id = db.Column(db.String(50), db.ForeignKey('sites.site_id'), nullable=False, index=True)
    row_number = db.Column(db.Integer)
    column_number = db.Column(db.Integer)
    string_number = db.Column(db.Integer)
    status = db.Column(db.String(50), default='NOT_INSPECTED')
    last_inspection = db.Column(db.DateTime)
    
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
            'row': self.row_number,
            'column': self.column_number,
            'status': self.status,
            'lastInspection': self.last_inspection.isoformat() if self.last_inspection else None
        }
        
        if latest:
            data['deltaTemp'] = latest.delta_temp
            data['issueType'] = latest.issue_type
        
        return data
    
    def __repr__(self):
        return f'<Panel {self.panel_id}>'
