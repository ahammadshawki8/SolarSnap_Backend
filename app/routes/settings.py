from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
import json

bp = Blueprint('settings', __name__)

# Default settings structure
DEFAULT_SETTINGS = {
    'thermalDetection': {
        'warningThreshold': 8.0,
        'criticalThreshold': 15.0,
        'hotspotDetection': True
    },
    'camera': {
        'palette': 'Iron',
        'resolution': '640x480'
    },
    'inspection': {
        'autoSave': True,
        'requirePanelScan': True
    },
    'connectivity': {
        'cloudSync': True,
        'autoUpload': True
    }
}

# Company default settings by company ID
COMPANY_SETTINGS = {
    'SOLARTECH-001': {
        'defaultThresholds': {
            'warning': 8.0,
            'critical': 15.0
        },
        'requiredFields': ['panelId', 'gps', 'thermalImage']
    },
    'SOLARTECH-002': {
        'defaultThresholds': {
            'warning': 10.0,
            'critical': 18.0
        },
        'requiredFields': ['panelId', 'thermalImage']
    },
    'SOLARTECH-003': {
        'defaultThresholds': {
            'warning': 7.0,
            'critical': 12.0
        },
        'requiredFields': ['panelId', 'gps', 'thermalImage', 'visualImage']
    }
}


@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_settings():
    """Get user-specific settings"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user settings from database or return defaults
        # For now, we'll use a simple approach with a settings column
        # In production, you might want a separate settings table
        
        # Check if user has custom settings stored
        if hasattr(user, 'settings') and user.settings:
            try:
                user_settings = json.loads(user.settings)
            except:
                user_settings = DEFAULT_SETTINGS.copy()
        else:
            user_settings = DEFAULT_SETTINGS.copy()
        
        return jsonify({
            'success': True,
            'settings': user_settings
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving settings: {str(e)}'
        }), 500


@bp.route('/user', methods=['PUT'])
@jwt_required()
def update_user_settings():
    """Update user settings"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No settings data provided'
            }), 400
        
        # Get current settings or defaults
        if hasattr(user, 'settings') and user.settings:
            try:
                current_settings = json.loads(user.settings)
            except:
                current_settings = DEFAULT_SETTINGS.copy()
        else:
            current_settings = DEFAULT_SETTINGS.copy()
        
        # Update settings with provided data (merge)
        if 'thermalDetection' in data:
            current_settings['thermalDetection'].update(data['thermalDetection'])
        
        if 'camera' in data:
            current_settings['camera'].update(data['camera'])
        
        if 'inspection' in data:
            current_settings['inspection'].update(data['inspection'])
        
        if 'connectivity' in data:
            current_settings['connectivity'].update(data['connectivity'])
        
        # Save updated settings
        user.settings = json.dumps(current_settings)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': current_settings
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        }), 500


@bp.route('/company/<company_id>', methods=['GET'])
@jwt_required()
def get_company_settings(company_id):
    """Get company-wide default settings"""
    try:
        # Verify user has access to this company
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Check if user belongs to this company (optional security check)
        if user.company_id != company_id:
            return jsonify({
                'success': False,
                'message': 'Access denied: You do not belong to this company'
            }), 403
        
        # Get company settings
        company_settings = COMPANY_SETTINGS.get(company_id)
        
        if not company_settings:
            # Return default company settings if not found
            company_settings = {
                'defaultThresholds': {
                    'warning': 8.0,
                    'critical': 15.0
                },
                'requiredFields': ['panelId', 'gps', 'thermalImage']
            }
        
        return jsonify({
            'success': True,
            'companySettings': {
                'companyId': company_id,
                **company_settings
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving company settings: {str(e)}'
        }), 500
