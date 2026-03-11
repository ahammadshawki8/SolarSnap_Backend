from app import db
from datetime import datetime

class UploadQueue(db.Model):
    __tablename__ = 'upload_queue'
    
    upload_id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspections.inspection_id'), nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, uploading, uploaded, failed
    file_size = db.Column(db.Float)  # in MB
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempt_at = db.Column(db.DateTime)
    
    # Relationship
    inspection = db.relationship('Inspection', backref='upload_queue')
    
    def to_dict(self):
        """Convert upload queue item to dictionary"""
        return {
            'uploadId': f"upload_{self.upload_id}",
            'inspectionId': self.inspection.inspection_uuid if self.inspection else None,
            'panelId': self.inspection.panel_id if self.inspection else None,
            'status': self.status,
            'fileSize': self.file_size,
            'retryCount': self.retry_count,
            'lastAttempt': int(self.last_attempt_at.timestamp() * 1000) if self.last_attempt_at else None,
            'errorMessage': self.error_message
        }
    
    def __repr__(self):
        return f'<UploadQueue {self.upload_id}>'
