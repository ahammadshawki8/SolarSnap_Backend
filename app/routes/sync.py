from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.upload_queue import UploadQueue
from app.models.inspection import Inspection
from datetime import datetime

bp = Blueprint('sync', __name__)

@bp.route('/status', methods=['GET'])
@jwt_required()
def get_sync_status():
    """Get current sync status for inspector"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get inspections for current user
        user_inspections = Inspection.query.filter_by(inspector_id=current_user_id).all()
        inspection_ids = [i.inspection_id for i in user_inspections]
        
        # Get upload queue items for user's inspections
        pending = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'pending'
        ).count()
        
        uploading = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'uploading'
        ).count()
        
        completed = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'uploaded'
        ).count()
        
        failed = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'failed'
        ).count()
        
        # Get last sync time
        last_sync_item = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'uploaded'
        ).order_by(UploadQueue.last_attempt_at.desc()).first()
        
        last_sync = int(last_sync_item.last_attempt_at.timestamp() * 1000) if last_sync_item and last_sync_item.last_attempt_at else None
        
        return jsonify({
            'success': True,
            'syncStatus': {
                'lastSync': last_sync,
                'pending': pending,
                'uploading': uploading,
                'completed': completed,
                'failed': failed
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/queue', methods=['GET'])
@jwt_required()
def get_sync_queue():
    """Get list of pending uploads"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get inspections for current user
        user_inspections = Inspection.query.filter_by(inspector_id=current_user_id).all()
        inspection_ids = [i.inspection_id for i in user_inspections]
        
        # Get queue items
        status_filter = request.args.get('status')
        
        query = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids)
        )
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        queue_items = query.order_by(UploadQueue.created_at.desc()).all()
        
        queue_data = [item.to_dict() for item in queue_items]
        
        return jsonify({
            'success': True,
            'queue': queue_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/retry/<int:upload_id>', methods=['POST'])
@jwt_required()
def retry_upload(upload_id):
    """Retry a failed upload"""
    try:
        upload_item = UploadQueue.query.get(upload_id)
        
        if not upload_item:
            return jsonify({
                'success': False,
                'error': {'message': f'Upload {upload_id} not found'}
            }), 404
        
        # Check if upload belongs to current user
        current_user_id = get_jwt_identity()
        inspection = Inspection.query.get(upload_item.inspection_id)
        
        if not inspection or inspection.inspector_id != current_user_id:
            return jsonify({
                'success': False,
                'error': {'message': 'Unauthorized'}
            }), 403
        
        # Update status to uploading
        upload_item.status = 'uploading'
        upload_item.last_attempt_at = datetime.utcnow()
        upload_item.retry_count += 1
        upload_item.error_message = None
        
        db.session.commit()
        
        # In a real implementation, this would trigger actual upload
        # For now, we'll simulate success
        upload_item.status = 'uploaded'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'status': 'uploaded',
            'message': 'Upload retry initiated'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/create', methods=['POST'])
@jwt_required()
def create_upload_queue():
    """Create upload queue item for an inspection"""
    try:
        data = request.get_json()
        
        inspection_id = data.get('inspectionId')
        if not inspection_id:
            return jsonify({
                'success': False,
                'error': {'message': 'inspectionId required'}
            }), 400
        
        # Get inspection by UUID
        inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
        
        if not inspection:
            return jsonify({
                'success': False,
                'error': {'message': 'Inspection not found'}
            }), 404
        
        # Check if queue item already exists
        existing = UploadQueue.query.filter_by(inspection_id=inspection.inspection_id).first()
        if existing:
            return jsonify({
                'success': False,
                'error': {'message': 'Upload queue item already exists'}
            }), 409
        
        # Create queue item
        queue_item = UploadQueue(
            inspection_id=inspection.inspection_id,
            status='pending',
            file_size=data.get('fileSize', 0)
        )
        
        db.session.add(queue_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'uploadId': f"upload_{queue_item.upload_id}",
            'message': 'Upload queued successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/clear-completed', methods=['POST'])
@jwt_required()
def clear_completed():
    """Clear completed uploads from queue"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get inspections for current user
        user_inspections = Inspection.query.filter_by(inspector_id=current_user_id).all()
        inspection_ids = [i.inspection_id for i in user_inspections]
        
        # Delete completed uploads
        deleted = UploadQueue.query.filter(
            UploadQueue.inspection_id.in_(inspection_ids),
            UploadQueue.status == 'uploaded'
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted} completed uploads'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
