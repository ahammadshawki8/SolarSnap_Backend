from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'companyId']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': {'message': f'Missing required field: {field}'}}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': {'message': 'Email already registered'}}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            full_name=data.get('fullName', ''),
            role=data.get('role', 'Field Engineer'),
            company_id=data['companyId']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': {'message': 'Email and password required'}}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        # Check password
        if not user or not user.check_password(data['password']):
            return jsonify({'success': False, 'error': {'message': 'Invalid email or password'}}), 401
        
        # Check company ID if provided
        if data.get('companyId') and user.company_id != data['companyId']:
            return jsonify({'success': False, 'error': {'message': 'Invalid company ID'}}), 401
        
        # Create tokens
        access_token = create_access_token(identity=user.user_id)
        refresh_token = create_refresh_token(identity=user.user_id)
        
        return jsonify({
            'success': True,
            'token': access_token,
            'refreshToken': refresh_token,
            'expiresIn': 3600,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'success': True,
            'token': access_token,
            'expiresIn': 3600
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard tokens)"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'error': {'message': 'User not found'}}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': str(e)}}), 500
