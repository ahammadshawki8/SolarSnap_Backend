from app import db
from datetime import datetime
import uuid

class Inspection(db.Model):
    __tablename__ = 'inspections'
    
    inspection_id = db.Column(db.Integer, primary_key=True)
    inspection_uuid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    site_id = db.Column(db.String(50), db.ForeignKey('sites.site_id'), nullable=False, index=True)
    panel_id = db.Column(db.String(50), db.ForeignKey('panels.panel_id'), nullable=False, index=True)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    temperature = db.Column(db.Float)
    delta_temp = db.Column(db.Float)
    severity = db.Column(db.String(20), index=True)  # HEALTHY, WARNING, CRITICAL
    issue_type = db.Column(db.String(50))  # hotspot, diode, connection, shading, none
    
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    thermal_image_url = db.Column(db.Text)
    visual_image_url = db.Column(db.Text)
    
    inspection_metadata = db.Column(db.JSON)  # Renamed from 'metadata' to avoid conflict
    
    # Property to access metadata with the expected name
    @property
    def metadata(self):
        return self.inspection_metadata
    
    @metadata.setter
    def metadata(self, value):
        self.inspection_metadata = value
    
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Inspection, self).__init__(**kwargs)
        if not self.inspection_uuid:
            self.inspection_uuid = f"insp_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}"
    
    def to_dict(self, include_details=False):
        """Convert inspection to dictionary"""
        data = {
            'inspectionId': self.inspection_uuid,
            'panelId': self.panel_id,
            'severity': self.severity,
            'issueType': self.issue_type,
            'deltaTemp': self.delta_temp,
            'timestamp': int(self.timestamp.timestamp() * 1000) if self.timestamp else None,
            'inspectorName': self.inspector.full_name if self.inspector else 'Unknown'
        }
        
        if self.thermal_image_url:
            data['thermalImageUrl'] = self.thermal_image_url
        
        if include_details:
            data.update({
                'siteId': self.site_id,
                'temperature': self.temperature,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'visualImageUrl': self.visual_image_url,
                'metadata': self.inspection_metadata
            })
        
        return data
    
    def __repr__(self):
        return f'<Inspection {self.inspection_uuid}>'
