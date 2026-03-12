from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.inspection import Inspection
from app.models.site import Site
from app.models.panel import Panel
from datetime import datetime, timedelta
from collections import Counter
import io
import csv

bp = Blueprint('reports', __name__)

@bp.route('/site/<site_id>', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_site_report(site_id):
    """Generate site inspection summary"""
    try:
        # Get query parameters
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        format_type = request.args.get('format', 'json')
        
        # Get site
        site = Site.query.get(site_id)
        if not site:
            return jsonify({
                'success': False,
                'error': {'message': f'Site {site_id} not found'}
            }), 404
        
        # Build query
        query = Inspection.query.filter_by(site_id=site_id)
        
        if start_date:
            start_dt = datetime.fromtimestamp(int(start_date) / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromtimestamp(int(end_date) / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        inspections = query.all()
        
        # Calculate statistics
        total_inspected = len(inspections)
        coverage = (total_inspected / site.total_panels * 100) if site.total_panels > 0 else 0
        
        critical = sum(1 for i in inspections if i.severity == 'CRITICAL')
        warnings = sum(1 for i in inspections if i.severity == 'WARNING')
        healthy = sum(1 for i in inspections if i.severity == 'HEALTHY')
        
        # Fault types
        fault_types = {}
        for inspection in inspections:
            if inspection.issue_type and inspection.issue_type != 'none':
                fault_types[inspection.issue_type] = fault_types.get(inspection.issue_type, 0) + 1
        
        # Temperature statistics
        temps = [i.temperature for i in inspections if i.temperature]
        avg_temp = sum(temps) / len(temps) if temps else 0
        max_temp = max(temps) if temps else 0
        
        # Max anomaly
        deltas = [i.delta_temp for i in inspections if i.delta_temp]
        max_anomaly = max(deltas) if deltas else 0
        
        report = {
            'siteId': site_id,
            'siteName': site.site_name,
            'summary': {
                'totalPanels': site.total_panels,
                'inspected': total_inspected,
                'coverage': round(coverage, 1)
            },
            'faultDistribution': {
                'critical': critical,
                'warning': warnings,
                'healthy': healthy
            },
            'faultTypes': fault_types,
            'temperatureStats': {
                'average': round(avg_temp, 1),
                'maximum': round(max_temp, 1),
                'maxAnomaly': round(max_anomaly, 1)
            }
        }
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/fault', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_fault_report():
    """Fault-specific report"""
    try:
        site_id = request.args.get('siteId')
        severity = request.args.get('severity')
        
        # Build query
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if severity:
            query = query.filter_by(severity=severity)
        else:
            # Only faults (not healthy)
            query = query.filter(Inspection.severity.in_(['WARNING', 'CRITICAL']))
        
        faults = query.order_by(Inspection.severity.desc(), Inspection.delta_temp.desc()).all()
        
        # Group by issue type
        by_type = {}
        for fault in faults:
            issue_type = fault.issue_type or 'unknown'
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append({
                'panelId': fault.panel_id,
                'severity': fault.severity,
                'deltaTemp': fault.delta_temp,
                'timestamp': int(fault.timestamp.timestamp() * 1000)
            })
        
        # Priority list (critical first)
        priority_faults = [
            {
                'panelId': f.panel_id,
                'severity': f.severity,
                'issueType': f.issue_type,
                'deltaTemp': f.delta_temp,
                'temperature': f.temperature,
                'location': f'{f.latitude}, {f.longitude}' if f.latitude else None
            }
            for f in faults[:20]  # Top 20
        ]
        
        return jsonify({
            'success': True,
            'report': {
                'totalFaults': len(faults),
                'byType': by_type,
                'priorityFaults': priority_faults
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/maintenance', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_maintenance_report():
    """Maintenance action recommendations"""
    try:
        site_id = request.args.get('siteId')
        
        # Get critical and warning inspections
        query = Inspection.query.filter(
            Inspection.severity.in_(['WARNING', 'CRITICAL'])
        )
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        issues = query.order_by(Inspection.severity.desc()).all()
        
        # Generate recommendations
        recommendations = []
        
        # Group by issue type
        by_type = {}
        for issue in issues:
            issue_type = issue.issue_type or 'unknown'
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        # Create recommendations
        for issue_type, items in by_type.items():
            critical_count = sum(1 for i in items if i.severity == 'CRITICAL')
            warning_count = sum(1 for i in items if i.severity == 'WARNING')
            
            priority = 'HIGH' if critical_count > 0 else 'MEDIUM'
            
            # Generate action based on issue type
            actions = {
                'hotspot': 'Inspect for debris, shading, or connection issues. Clean panels if necessary.',
                'diode_failure': 'Replace bypass diode. Panel may need replacement if issue persists.',
                'cell_crack': 'Monitor for performance degradation. Consider panel replacement.',
                'connection_fault': 'Check wiring connections and junction box. Tighten or replace connections.',
                'shading': 'Identify and remove shading source. Trim vegetation if applicable.'
            }
            
            action = actions.get(issue_type, 'Inspect panel and determine appropriate action.')
            
            recommendations.append({
                'issueType': issue_type,
                'priority': priority,
                'affectedPanels': len(items),
                'critical': critical_count,
                'warnings': warning_count,
                'recommendedAction': action,
                'panels': [i.panel_id for i in items[:10]]  # First 10
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: (x['priority'] == 'HIGH', x['critical']), reverse=True)
        
        return jsonify({
            'success': True,
            'report': {
                'totalIssues': len(issues),
                'recommendations': recommendations
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/export', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def export_report():
    """Export report as PDF/CSV and optionally email"""
    try:
        data = request.get_json()
        
        report_type = data.get('reportType', 'site')
        site_id = data.get('siteId')
        format_type = data.get('format', 'csv')
        date_range = data.get('dateRange', {})
        
        # Get inspections
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if date_range.get('start'):
            start_dt = datetime.fromtimestamp(date_range['start'] / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if date_range.get('end'):
            end_dt = datetime.fromtimestamp(date_range['end'] / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        inspections = query.all()
        
        if format_type == 'csv':
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Inspection ID', 'Site ID', 'Panel ID', 'Temperature', 
                'Delta Temp', 'Severity', 'Issue Type', 'Latitude', 
                'Longitude', 'Timestamp', 'Inspector'
            ])
            
            # Data
            for insp in inspections:
                writer.writerow([
                    insp.inspection_uuid,
                    insp.site_id,
                    insp.panel_id,
                    insp.temperature,
                    insp.delta_temp,
                    insp.severity,
                    insp.issue_type,
                    insp.latitude,
                    insp.longitude,
                    insp.timestamp.isoformat(),
                    insp.inspector.full_name if insp.inspector else 'Unknown'
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            output.close()
            
            # In production, save to file and return URL
            filename = f"report_{site_id}_{int(datetime.now().timestamp())}.csv"
            download_url = f"/downloads/{filename}"
            
            return jsonify({
                'success': True,
                'downloadUrl': download_url,
                'format': 'csv',
                'records': len(inspections),
                'expiresAt': int((datetime.now() + timedelta(days=7)).timestamp() * 1000),
                'emailSent': data.get('email') is not None
            }), 200
        
        elif format_type == 'pdf':
            # For PDF, we'd use ReportLab here
            # Simplified response for now
            filename = f"report_{site_id}_{int(datetime.now().timestamp())}.pdf"
            download_url = f"/downloads/{filename}"
            
            return jsonify({
                'success': True,
                'downloadUrl': download_url,
                'format': 'pdf',
                'records': len(inspections),
                'expiresAt': int((datetime.now() + timedelta(days=7)).timestamp() * 1000),
                'emailSent': data.get('email') is not None
            }), 200
        
        else:
            return jsonify({
                'success': False,
                'error': {'message': 'Invalid format. Use csv or pdf'}
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/temperature-distribution', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_temperature_distribution():
    """Get temperature distribution for charts"""
    try:
        site_id = request.args.get('siteId')
        
        query = Inspection.query
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        inspections = query.all()
        
        # Create temperature ranges
        ranges = {
            '0-30': 0,
            '30-35': 0,
            '35-40': 0,
            '40-45': 0,
            '45-50': 0,
            '50+': 0
        }
        
        for insp in inspections:
            if not insp.temperature:
                continue
            
            temp = insp.temperature
            if temp < 30:
                ranges['0-30'] += 1
            elif temp < 35:
                ranges['30-35'] += 1
            elif temp < 40:
                ranges['35-40'] += 1
            elif temp < 45:
                ranges['40-45'] += 1
            elif temp < 50:
                ranges['45-50'] += 1
            else:
                ranges['50+'] += 1
        
        return jsonify({
            'success': True,
            'distribution': ranges
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

@bp.route('/generate', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def generate_report():
    """Generate report based on request parameters"""
    try:
        data = request.get_json() or {}
        
        report_type = data.get('reportType', 'site')
        site_id = data.get('siteId')
        date_range = data.get('dateRange', {})
        
        # Build query based on parameters
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if date_range.get('start'):
            start_dt = datetime.fromtimestamp(date_range['start'] / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if date_range.get('end'):
            end_dt = datetime.fromtimestamp(date_range['end'] / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        inspections = query.all()
        
        # Generate report based on type
        if report_type == 'fault':
            # Fault report
            faults = [i for i in inspections if i.severity in ['WARNING', 'CRITICAL']]
            
            fault_summary = {}
            for fault in faults:
                issue_type = fault.issue_type or 'unknown'
                if issue_type not in fault_summary:
                    fault_summary[issue_type] = {'count': 0, 'critical': 0, 'warning': 0}
                
                fault_summary[issue_type]['count'] += 1
                if fault.severity == 'CRITICAL':
                    fault_summary[issue_type]['critical'] += 1
                else:
                    fault_summary[issue_type]['warning'] += 1
            
            report_data = {
                'reportType': 'fault',
                'totalFaults': len(faults),
                'faultSummary': fault_summary,
                'generatedAt': int(datetime.utcnow().timestamp() * 1000)
            }
            
        elif report_type == 'maintenance':
            # Maintenance report
            critical_issues = [i for i in inspections if i.severity == 'CRITICAL']
            warning_issues = [i for i in inspections if i.severity == 'WARNING']
            
            recommendations = []
            
            # Group by issue type for recommendations
            issue_groups = {}
            for issue in critical_issues + warning_issues:
                issue_type = issue.issue_type or 'unknown'
                if issue_type not in issue_groups:
                    issue_groups[issue_type] = []
                issue_groups[issue_type].append(issue)
            
            for issue_type, issues in issue_groups.items():
                critical_count = sum(1 for i in issues if i.severity == 'CRITICAL')
                priority = 'HIGH' if critical_count > 0 else 'MEDIUM'
                
                recommendations.append({
                    'issueType': issue_type,
                    'priority': priority,
                    'affectedPanels': len(issues),
                    'recommendedAction': f'Inspect and repair {issue_type} issues'
                })
            
            report_data = {
                'reportType': 'maintenance',
                'totalIssues': len(critical_issues) + len(warning_issues),
                'recommendations': recommendations,
                'generatedAt': int(datetime.utcnow().timestamp() * 1000)
            }
            
        else:
            # Site summary report (default)
            site = Site.query.get(site_id) if site_id else None
            
            total_inspected = len(inspections)
            critical = sum(1 for i in inspections if i.severity == 'CRITICAL')
            warnings = sum(1 for i in inspections if i.severity == 'WARNING')
            healthy = sum(1 for i in inspections if i.severity == 'HEALTHY')
            
            # Temperature stats
            temps = [i.temperature for i in inspections if i.temperature]
            avg_temp = sum(temps) / len(temps) if temps else 0
            max_temp = max(temps) if temps else 0
            
            report_data = {
                'reportType': 'site',
                'siteId': site_id,
                'siteName': site.site_name if site else 'All Sites',
                'summary': {
                    'totalInspected': total_inspected,
                    'critical': critical,
                    'warnings': warnings,
                    'healthy': healthy
                },
                'temperatureStats': {
                    'average': round(avg_temp, 1),
                    'maximum': round(max_temp, 1)
                },
                'generatedAt': int(datetime.utcnow().timestamp() * 1000)
            }
        
        return jsonify({
            'success': True,
            'report': report_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/export-data', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def export_data():
    """Export inspection data in various formats"""
    try:
        data = request.get_json() or {}
        
        export_format = data.get('format', 'csv')
        site_id = data.get('siteId')
        date_range = data.get('dateRange', {})
        
        # Build query
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if date_range.get('start'):
            start_dt = datetime.fromtimestamp(date_range['start'] / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if date_range.get('end'):
            end_dt = datetime.fromtimestamp(date_range['end'] / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        inspections = query.all()
        
        # Generate filename
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"solarsnap_export_{timestamp}.{export_format}"
        
        if export_format == 'csv':
            # Generate CSV data (simplified for demo)
            csv_data = "Panel ID,Site ID,Temperature,Delta Temp,Severity,Issue Type,Timestamp\n"
            
            for inspection in inspections:
                csv_data += f"{inspection.panel_id},{inspection.site_id},{inspection.temperature},{inspection.delta_temp},{inspection.severity},{inspection.issue_type},{inspection.timestamp}\n"
            
            # In a real implementation, you'd save this to a file and return a download URL
            download_url = f"/downloads/{filename}"
            
        elif export_format == 'json':
            # Generate JSON export
            export_data = {
                'exportInfo': {
                    'generatedAt': datetime.utcnow().isoformat(),
                    'totalRecords': len(inspections),
                    'siteId': site_id,
                    'dateRange': date_range
                },
                'inspections': [inspection.to_dict(include_details=True) for inspection in inspections]
            }
            
            download_url = f"/downloads/{filename}"
            
        else:
            return jsonify({
                'success': False,
                'error': {'message': f'Unsupported export format: {export_format}'}
            }), 400
        
        return jsonify({
            'success': True,
            'downloadUrl': download_url,
            'filename': filename,
            'format': export_format,
            'recordCount': len(inspections),
            'expiresAt': int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/dashboard-stats', methods=['GET'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def get_dashboard_stats():
    """Get dashboard statistics for reports page"""
    try:
        site_id = request.args.get('siteId')
        
        # Build base query
        query = Inspection.query
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        # Get today's inspections
        today = datetime.utcnow().date()
        today_inspections = query.filter(
            db.func.date(Inspection.timestamp) == today
        ).all()
        
        # Get all inspections for overall stats
        all_inspections = query.all()
        
        # Calculate stats
        today_stats = {
            'total': len(today_inspections),
            'critical': sum(1 for i in today_inspections if i.severity == 'CRITICAL'),
            'warnings': sum(1 for i in today_inspections if i.severity == 'WARNING'),
            'healthy': sum(1 for i in today_inspections if i.severity == 'HEALTHY')
        }
        
        overall_stats = {
            'total': len(all_inspections),
            'critical': sum(1 for i in all_inspections if i.severity == 'CRITICAL'),
            'warnings': sum(1 for i in all_inspections if i.severity == 'WARNING'),
            'healthy': sum(1 for i in all_inspections if i.severity == 'HEALTHY')
        }
        
        # Issue type breakdown
        issue_breakdown = {}
        for inspection in all_inspections:
            if inspection.issue_type and inspection.issue_type != 'none':
                issue_type = inspection.issue_type
                if issue_type not in issue_breakdown:
                    issue_breakdown[issue_type] = 0
                issue_breakdown[issue_type] += 1
        
        # Temperature distribution
        temps = [i.temperature for i in all_inspections if i.temperature]
        temp_stats = {
            'average': round(sum(temps) / len(temps), 1) if temps else 0,
            'minimum': round(min(temps), 1) if temps else 0,
            'maximum': round(max(temps), 1) if temps else 0
        }
        
        return jsonify({
            'success': True,
            'stats': {
                'today': today_stats,
                'overall': overall_stats,
                'issueBreakdown': issue_breakdown,
                'temperatureStats': temp_stats,
                'lastUpdated': int(datetime.utcnow().timestamp() * 1000)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/export-history', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def export_history():
    """Export inspection history records"""
    try:
        data = request.get_json() or {}
        
        export_format = data.get('format', 'csv').lower()
        site_id = data.get('siteId')
        panel_id = data.get('panelId')
        severity_filter = data.get('severity')
        date_range = data.get('dateRange', {})
        
        # Build query
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if panel_id:
            query = query.filter_by(panel_id=panel_id)
        
        if severity_filter and severity_filter != 'all':
            if severity_filter == 'faults':
                query = query.filter(Inspection.severity.in_(['WARNING', 'CRITICAL']))
            else:
                query = query.filter_by(severity=severity_filter.upper())
        
        if date_range.get('start'):
            start_dt = datetime.fromtimestamp(date_range['start'] / 1000)
            query = query.filter(Inspection.timestamp >= start_dt)
        
        if date_range.get('end'):
            end_dt = datetime.fromtimestamp(date_range['end'] / 1000)
            query = query.filter(Inspection.timestamp <= end_dt)
        
        inspections = query.order_by(Inspection.timestamp.desc()).all()
        
        # Generate filename
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"inspection_history_{timestamp}.{export_format}"
        
        if export_format == 'csv':
            # Generate CSV data
            csv_data = "Inspection ID,Panel ID,Site ID,Temperature,Delta Temp,Severity,Issue Type,Latitude,Longitude,Timestamp,Inspector\n"
            
            for inspection in inspections:
                inspector_name = inspection.inspector.full_name if inspection.inspector else 'Unknown'
                csv_data += f'"{inspection.inspection_uuid}","{inspection.panel_id}","{inspection.site_id}",{inspection.temperature},{inspection.delta_temp},"{inspection.severity}","{inspection.issue_type}",{inspection.latitude},{inspection.longitude},"{inspection.timestamp.isoformat()}","{inspector_name}"\n'
            
        elif export_format == 'json':
            # Generate JSON export
            export_data = {
                'exportInfo': {
                    'generatedAt': datetime.utcnow().isoformat(),
                    'totalRecords': len(inspections),
                    'filters': {
                        'siteId': site_id,
                        'panelId': panel_id,
                        'severity': severity_filter,
                        'dateRange': date_range
                    }
                },
                'inspections': []
            }
            
            for inspection in inspections:
                export_data['inspections'].append({
                    'inspectionId': inspection.inspection_uuid,
                    'panelId': inspection.panel_id,
                    'siteId': inspection.site_id,
                    'temperature': inspection.temperature,
                    'deltaTemp': inspection.delta_temp,
                    'severity': inspection.severity,
                    'issueType': inspection.issue_type,
                    'latitude': inspection.latitude,
                    'longitude': inspection.longitude,
                    'timestamp': inspection.timestamp.isoformat(),
                    'inspector': inspection.inspector.full_name if inspection.inspector else 'Unknown'
                })
            
        elif export_format == 'pdf':
            # For PDF export (simplified response)
            filename = f"inspection_history_{timestamp}.pdf"
            
        else:
            return jsonify({
                'success': False,
                'error': {'message': f'Unsupported export format: {export_format}'}
            }), 400
        
        # In production, save file and return download URL
        download_url = f"/downloads/{filename}"
        
        return jsonify({
            'success': True,
            'downloadUrl': download_url,
            'filename': filename,
            'format': export_format,
            'recordCount': len(inspections),
            'expiresAt': int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/delete-record', methods=['DELETE'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def delete_inspection_record():
    """Delete a specific inspection record"""
    try:
        data = request.get_json() or {}
        inspection_id = data.get('inspectionId')
        
        if not inspection_id:
            return jsonify({
                'success': False,
                'error': {'message': 'Inspection ID is required'}
            }), 400
        
        # Find the inspection
        inspection = Inspection.query.filter_by(inspection_uuid=inspection_id).first()
        
        if not inspection:
            return jsonify({
                'success': False,
                'error': {'message': f'Inspection {inspection_id} not found'}
            }), 404
        
        # Store info for response
        panel_id = inspection.panel_id
        site_id = inspection.site_id
        
        # Delete the inspection
        db.session.delete(inspection)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Inspection record deleted successfully',
            'deletedRecord': {
                'inspectionId': inspection_id,
                'panelId': panel_id,
                'siteId': site_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@bp.route('/cloud-sync', methods=['POST'])
# @jwt_required()  # TODO: Re-enable authentication after frontend auth is implemented
def sync_to_cloud():
    """Sync inspection data to cloud dashboard"""
    try:
        data = request.get_json() or {}
        
        site_id = data.get('siteId')
        sync_type = data.get('syncType', 'incremental')  # 'full' or 'incremental'
        
        # Build query for data to sync
        query = Inspection.query
        
        if site_id:
            query = query.filter_by(site_id=site_id)
        
        if sync_type == 'incremental':
            # Only sync data from last 24 hours
            since = datetime.utcnow() - timedelta(days=1)
            query = query.filter(Inspection.timestamp >= since)
        
        inspections = query.all()
        
        # Simulate cloud sync process
        sync_stats = {
            'totalRecords': len(inspections),
            'critical': sum(1 for i in inspections if i.severity == 'CRITICAL'),
            'warnings': sum(1 for i in inspections if i.severity == 'WARNING'),
            'healthy': sum(1 for i in inspections if i.severity == 'HEALTHY'),
            'thermalImages': len([i for i in inspections if i.thermal_image_path]),
            'gpsCoordinates': len([i for i in inspections if i.latitude and i.longitude])
        }
        
        # In a real implementation, this would:
        # 1. Upload thermal images to cloud storage
        # 2. Send inspection data to cloud API
        # 3. Update sync status in database
        
        return jsonify({
            'success': True,
            'message': 'Data synchronized to cloud successfully',
            'syncStats': sync_stats,
            'syncId': f"sync_{int(datetime.utcnow().timestamp())}",
            'syncedAt': int(datetime.utcnow().timestamp() * 1000),
            'cloudDashboardUrl': 'https://dashboard.solarsnap.com'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500