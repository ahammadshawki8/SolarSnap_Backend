from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.site import Site
from app.models.panel import Panel
from app.models.inspection import Inspection
from datetime import datetime

bp = Blueprint('sites', __name__)

@bp.route('', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_sites():
    """Get list of sites assigned to inspector"""
    try:
        # Get query parameters
        company_id = request.args.get('companyId')
        status = request.args.get('status')
        
        # Build query
        query = Site.query
        
        if company_id:
            # In production, filter by user's company
            pass
        
        if status:
            query = query.filter_by(status=status)
        
        sites = query.all()
        
        # Get today's inspection count for each site
        today = datetime.utcnow().date()
        sites_data = []
        
        for site in sites:
            inspections_today = Inspection.query.filter(
                Inspection.site_id == site.site_id,
                db.func.date(Inspection.timestamp) == today
            ).count()
            
            # Get last inspection time
            last_inspection = Inspection.query.filter_by(
                site_id=site.site_id
            ).order_by(Inspection.timestamp.desc()).first()
            
            site_dict = site.to_dict()
            site_dict['inspectedToday'] = inspections_today
            site_dict['lastInspection'] = int(last_inspection.timestamp.timestamp() * 1000) if last_inspection else None
            
            sites_data.append(site_dict)
        
        return jsonify({
            'success': True,
            'sites': sites_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/<site_id>', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_site_details(site_id):
    """Get detailed site information"""
    try:
        site = Site.query.get(site_id)
        
        if not site:
            return jsonify({
                'success': False,
                'error': {'message': f'Site {site_id} not found'}
            }), 404
        
        # Get statistics
        site_dict = site.to_dict(include_stats=True)
        
        return jsonify({
            'success': True,
            'site': site_dict
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/<site_id>/panels', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_site_panels(site_id):
    """Get panel layout and status for map view - optimized for large datasets"""
    try:
        site = Site.query.get(site_id)
        
        if not site:
            return jsonify({
                'success': False,
                'error': {'message': f'Site {site_id} not found'}
            }), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # Reduced default to 100
        per_page = min(per_page, 200)  # Max 200 panels per request
        
        # Get paginated panels for this site
        pagination = Panel.query.filter_by(site_id=site_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Return minimal data for map view (only what's needed)
        panels_data = [{
            'panel_id': panel.panel_id,
            'row_number': panel.row_number,
            'column_number': panel.column_number,
            'status': panel.status,
            'last_inspection': panel.last_inspection.isoformat() if panel.last_inspection else None
        } for panel in pagination.items]
        
        return jsonify({
            'success': True,
            'panels': panels_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def create_site():
    """Create a new site (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['siteId', 'siteName', 'totalPanels']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {'message': f'Missing required field: {field}'}
                }), 400
        
        # Check if site already exists
        if Site.query.get(data['siteId']):
            return jsonify({
                'success': False,
                'error': {'message': 'Site ID already exists'}
            }), 409
        
        # Create new site
        site = Site(
            site_id=data['siteId'],
            site_name=data['siteName'],
            total_panels=data['totalPanels'],
            rows=data.get('rows', 0),
            panels_per_row=data.get('panelsPerRow', 0),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            status=data.get('status', 'active')
        )
        
        db.session.add(site)
        
        # Create panels if layout information is provided
        rows = data.get('rows', 0)
        panels_per_row = data.get('panelsPerRow', 0)
        total_panels = data['totalPanels']
        
        # Check if panels already exist for this site (cleanup any partial creation)
        from app.models.panel import Panel
        existing_panels = Panel.query.filter_by(site_id=data['siteId']).all()
        if existing_panels:
            for panel in existing_panels:
                db.session.delete(panel)
            db.session.flush()  # Ensure deletions are processed before inserts
        
        if rows > 0 and panels_per_row > 0:
            # Create panels based on grid layout
            from app.models.panel import Panel
            
            panel_count = 0
            for row in range(1, rows + 1):
                for col in range(1, panels_per_row + 1):
                    if panel_count >= total_panels:
                        break
                    
                    # Create globally unique panel ID: SITE-ID-R##C##
                    # Example: NV-SOLAR-05-R01C01, NV-SOLAR-05-R01C02, etc.
                    panel_id = f"{data['siteId']}-R{row:02d}C{col:02d}"
                    
                    panel = Panel(
                        panel_id=panel_id,
                        site_id=data['siteId'],
                        row_number=row,
                        column_number=col,
                        string_number=((col - 1) // 10) + 1,  # 10 panels per string
                        status='uninspected'
                    )
                    db.session.add(panel)
                    panel_count += 1
                
                if panel_count >= total_panels:
                    break
        else:
            # Create panels with sequential numbering if no layout specified
            from app.models.panel import Panel
            
            for i in range(1, total_panels + 1):
                # Create globally unique panel ID: SITE-ID-P####
                # Example: NV-SOLAR-05-P0001, NV-SOLAR-05-P0002, etc.
                panel_id = f"{data['siteId']}-P{i:04d}"
                panel = Panel(
                    panel_id=panel_id,
                    site_id=data['siteId'],
                    row_number=1,
                    column_number=i,
                    string_number=((i - 1) // 10) + 1,
                    status='uninspected'
                )
                db.session.add(panel)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Site created successfully with {total_panels} panels',
            'site': site.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
