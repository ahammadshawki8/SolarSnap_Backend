from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from app.models.inspection import Inspection
from app.models.upload_queue import UploadQueue
import os
from datetime import datetime
import io

# Try to import Pillow, but make it optional
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow not available. Image compression disabled.")

bp = Blueprint('uploads', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def compress_image(file_data, quality=85):
    """Compress image to reduce file size"""
    if not PILLOW_AVAILABLE:
        # Return original data if Pillow is not available
        return file_data, len(file_data)
    
    try:
        image = Image.open(io.BytesIO(file_data))
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Compress
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        return output.read()
    except Exception as e:
        # If compression fails, return original
        return file_data

@bp.route('/thermal', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def upload_thermal():
    """Upload thermal image file"""
    try:
        # Check if image is in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': {'message': 'No image provided'}
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': {'message': 'No file selected'}
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': {'message': 'Invalid file type. Allowed: jpg, jpeg, png'}
            }), 400
        
        # Get form data
        inspection_id = request.form.get('inspectionId')
        panel_id = request.form.get('panelId')
        timestamp = request.form.get('timestamp', str(int(datetime.now().timestamp() * 1000)))
        
        # Validate required fields
        if not panel_id:
            return jsonify({
                'success': False,
                'error': {'message': 'Panel ID is required'}
            }), 400
        
        # Read and compress file
        file_data = file.read()
        compressed_data = compress_image(file_data)
        
        # Generate filename
        filename = secure_filename(f"thermal_{panel_id}_{timestamp}.jpg")
        
        # Create thermal subfolder
        thermal_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thermal')
        os.makedirs(thermal_folder, exist_ok=True)
        
        # Save file
        filepath = os.path.join(thermal_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
        
        # Calculate file size in MB
        file_size = len(compressed_data) / (1024 * 1024)
        
        # Generate URL (in production, this would be CDN URL)
        image_url = f"/uploads/thermal/{filename}"
        
        # Update inspection if inspection_id provided
        if inspection_id:
            inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
            if inspection:
                inspection.thermal_image_url = image_url
                db.session.commit()
        
        return jsonify({
            'success': True,
            'imageId': f"img_thermal_{timestamp}",
            'url': image_url,
            'size': round(file_size, 2),
            'uploadedAt': int(datetime.now().timestamp() * 1000)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/visual', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def upload_visual():
    """Upload visual/RGB image"""
    try:
        # Check if image is in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': {'message': 'No image provided'}
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': {'message': 'No file selected'}
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': {'message': 'Invalid file type. Allowed: jpg, jpeg, png'}
            }), 400
        
        # Get form data
        inspection_id = request.form.get('inspectionId')
        panel_id = request.form.get('panelId')
        timestamp = request.form.get('timestamp', str(int(datetime.now().timestamp() * 1000)))
        
        # Read and compress file
        file_data = file.read()
        compressed_data = compress_image(file_data, quality=90)
        
        # Generate filename
        filename = secure_filename(f"visual_{panel_id}_{timestamp}.jpg")
        
        # Create visual subfolder
        visual_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'visual')
        os.makedirs(visual_folder, exist_ok=True)
        
        # Save file
        filepath = os.path.join(visual_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
        
        # Calculate file size in MB
        file_size = len(compressed_data) / (1024 * 1024)
        
        # Generate URL
        image_url = f"/uploads/visual/{filename}"
        
        # Update inspection if inspection_id provided
        if inspection_id:
            inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
            if inspection:
                inspection.visual_image_url = image_url
                db.session.commit()
        
        return jsonify({
            'success': True,
            'imageId': f"img_visual_{timestamp}",
            'url': image_url,
            'size': round(file_size, 2),
            'uploadedAt': int(datetime.now().timestamp() * 1000)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/batch', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def upload_batch():
    """Batch upload multiple inspections and images"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get JSON data for inspections
        inspections_data = request.form.get('inspections')
        if not inspections_data:
            return jsonify({
                'success': False,
                'error': {'message': 'No inspections data provided'}
            }), 400
        
        import json
        inspections = json.loads(inspections_data)
        
        # Get files
        thermal_images = request.files.getlist('thermalImages[]')
        visual_images = request.files.getlist('visualImages[]')
        
        results = []
        uploaded = 0
        failed = 0
        
        for idx, insp_data in enumerate(inspections):
            try:
                # Create inspection
                timestamp = datetime.fromtimestamp(insp_data['timestamp'] / 1000)
                
                inspection = Inspection(
                    site_id=insp_data['siteId'],
                    panel_id=insp_data['panelId'],
                    inspector_id=current_user_id,
                    temperature=insp_data['temperature'],
                    delta_temp=insp_data['deltaTemp'],
                    severity=insp_data['severity'],
                    issue_type=insp_data.get('issueType', 'none'),
                    latitude=insp_data.get('latitude'),
                    longitude=insp_data.get('longitude'),
                    metadata=insp_data.get('metadata', {}),
                    timestamp=timestamp
                )
                
                db.session.add(inspection)
                db.session.flush()  # Get inspection ID
                
                # Upload thermal image if provided
                thermal_url = None
                if idx < len(thermal_images):
                    thermal_file = thermal_images[idx]
                    if thermal_file and allowed_file(thermal_file.filename):
                        file_data = thermal_file.read()
                        compressed_data = compress_image(file_data)
                        
                        filename = secure_filename(f"thermal_{insp_data['panelId']}_{int(timestamp.timestamp() * 1000)}.jpg")
                        thermal_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thermal')
                        os.makedirs(thermal_folder, exist_ok=True)
                        
                        filepath = os.path.join(thermal_folder, filename)
                        with open(filepath, 'wb') as f:
                            f.write(compressed_data)
                        
                        thermal_url = f"/uploads/thermal/{filename}"
                        inspection.thermal_image_url = thermal_url
                
                # Upload visual image if provided
                visual_url = None
                if idx < len(visual_images):
                    visual_file = visual_images[idx]
                    if visual_file and allowed_file(visual_file.filename):
                        file_data = visual_file.read()
                        compressed_data = compress_image(file_data, quality=90)
                        
                        filename = secure_filename(f"visual_{insp_data['panelId']}_{int(timestamp.timestamp() * 1000)}.jpg")
                        visual_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'visual')
                        os.makedirs(visual_folder, exist_ok=True)
                        
                        filepath = os.path.join(visual_folder, filename)
                        with open(filepath, 'wb') as f:
                            f.write(compressed_data)
                        
                        visual_url = f"/uploads/visual/{filename}"
                        inspection.visual_image_url = visual_url
                
                db.session.commit()
                
                results.append({
                    'inspectionId': inspection.inspection_uuid,
                    'status': 'success',
                    'thermalImageUrl': thermal_url,
                    'visualImageUrl': visual_url
                })
                uploaded += 1
                
            except Exception as e:
                db.session.rollback()
                results.append({
                    'panelId': insp_data.get('panelId', 'unknown'),
                    'status': 'failed',
                    'error': str(e)
                })
                failed += 1
        
        return jsonify({
            'success': True,
            'uploaded': uploaded,
            'failed': failed,
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
