from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.inspection import Inspection
from app.models.panel import Panel
from app.models.site import Site
from datetime import datetime

bp = Blueprint('inspections', __name__)

@bp.route('', methods=['POST'])
@jwt_required()
def create_inspection():
    """Create new inspection record"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['siteId', 'panelId', 'temperature', 'deltaTemp', 'severity', 'timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {'message': f'Missing required field: {field}'}
                }), 400
        
        # Verify site exists
        site = Site.query.get(data['siteId'])
        if not site:
            return jsonify({
                'success': False,
                'error': {'message': f'Site {data["siteId"]} not found'}
            }), 404
        
        # Verify or create panel
        panel = Panel.query.get(data['panelId'])
        if not panel:
            # Auto-create panel if it doesn't exist
            panel = Panel(
                panel_id=data['panelId'],
                site_id=data['siteId'],
                status='NOT_INSPECTED'
            )
            db.session.add(panel)
        
        # Convert timestamp from milliseconds to datetime
        timestamp = datetime.fromtimestamp(data['timestamp'] / 1000)
        
        # Create inspection
        inspection = Inspection(
            site_id=data['siteId'],
            panel_id=data['panelId'],
            inspector_id=current_user_id,
            temperature=data['temperature'],
            delta_temp=data['deltaTemp'],
            severity=data['severity'],
            issue_type=data.get('issueType', 'none'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            thermal_image_url=data.get('thermalImageId'),
            visual_image_url=data.get('visualImageId'),
            metadata=data.get('metadata', {}),
            timestamp=timestamp
        )
        
        db.session.add(inspection)
        
        # Update panel status
        panel.status = data['severity']
        panel.last_inspection = timestamp
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'inspectionId': inspection.inspection_uuid,
            'message': 'Inspection recorded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('', methods=['GET'])
@jwt_required()
def get_inspections():
    """List inspections with filtering and pagination"""
    try:
        # Get query parameters
        site_id = request.args.get('siteId')
        panel_id = request.args.get('panelId')
        severity = request.args.get('severity')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if panel_id:
            query = query.filter_by(panel_id=panel_id)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if start_date:
            start_dt = datetime.fromtimestamp(int(start_date) / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromtimestamp(int(end_date) / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        inspections = query.order_by(Inspection.timestamp.desc()).limit(limit).offset(offset).all()
        
        inspections_data = [inspection.to_dict() for inspection in inspections]
        
        return jsonify({
            'success': True,
            'total': total,
            'inspections': inspections_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/<inspection_id>', methods=['GET'])
@jwt_required()
def get_inspection_details(inspection_id):
    """Get detailed inspection information"""
    try:
        inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
        
        if not inspection:
            return jsonify({
                'success': False,
                'error': {'message': f'Inspection {inspection_id} not found'}
            }), 404
        
        return jsonify({
            'success': True,
            'inspection': inspection.to_dict(include_details=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/<inspection_id>', methods=['DELETE'])
@jwt_required()
def delete_inspection(inspection_id):
    """Delete inspection record"""
    try:
        inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
        
        if not inspection:
            return jsonify({
                'success': False,
                'error': {'message': f'Inspection {inspection_id} not found'}
            }), 404
        
        # Update panel status if this was the last inspection
        panel = Panel.query.get(inspection.panel_id)
        if panel and panel.last_inspection == inspection.timestamp:
            # Find previous inspection
            prev_inspection = Inspection.query.filter(
                Inspection.panel_id == inspection.panel_id,
                Inspection.inspection_id != inspection.inspection_id
            ).order_by(Inspection.timestamp.desc()).first()
            
            if prev_inspection:
                panel.status = prev_inspection.severity
                panel.last_inspection = prev_inspection.timestamp
            else:
                panel.status = 'NOT_INSPECTED'
                panel.last_inspection = None
        
        db.session.delete(inspection)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Inspection deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/panel/<panel_id>', methods=['GET'])
@jwt_required()
def get_panel_inspections(panel_id):
    """Get all inspections for a specific panel"""
    try:
        inspections = Inspection.query.filter_by(panel_id=panel_id).order_by(Inspection.timestamp.desc()).all()
        
        if not inspections:
            return jsonify({
                'success': True,
                'inspections': [],
                'latest': None
            }), 200
        
        # Get latest inspection with full details
        latest_inspection = inspections[0]
        
        return jsonify({
            'success': True,
            'inspections': [inspection.to_dict() for inspection in inspections],
            'latest': latest_inspection.to_dict(include_details=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_inspection_statistics():
    """Get inspection statistics for dashboard"""
    try:
        site_id = request.args.get('siteId')
        
        query = Inspection.query
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        # Get today's inspections
        today = datetime.utcnow().date()
        today_inspections = query.filter(
            db.func.date(Inspection.timestamp) == today
        ).all()
        
        # Calculate statistics
        total = len(today_inspections)
        critical = sum(1 for i in today_inspections if i.severity == 'CRITICAL')
        warnings = sum(1 for i in today_inspections if i.severity == 'WARNING')
        healthy = sum(1 for i in today_inspections if i.severity == 'HEALTHY')
        
        # Fault types
        fault_types = {}
        for inspection in today_inspections:
            if inspection.issue_type and inspection.issue_type != 'none':
                fault_types[inspection.issue_type] = fault_types.get(inspection.issue_type, 0) + 1
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'critical': critical,
                'warnings': warnings,
                'healthy': healthy,
                'faultTypes': fault_types
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
