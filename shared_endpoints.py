from flask import Blueprint, jsonify, request
from auth import token_required
from models import db_connection

shared_bp = Blueprint('shared', __name__)


@shared_bp.route('/zones', methods=['GET'])
@token_required
def get_all_zones():
    """Get all active zones with basic information"""
    try:
        with db_connection.get_cursor() as cursor:
            # Get active zones
            cursor.execute("""
                SELECT 
                    z.id, z.name, z.description, z.cleanliness_score as cleanlinessScore, z.color
                FROM zones z
                WHERE z.is_active = true
                ORDER BY z.name
            """)
            zones = cursor.fetchall()
            
            # Get polygon points for each zone
            for zone in zones:
                cursor.execute("""
                    SELECT latitude, longitude, point_order
                    FROM zone_polygons
                    WHERE zone_id = %s
                    ORDER BY point_order
                """, (zone['id'],))
                polygon_points = cursor.fetchall()
                
                zone['polygon'] = [
                    {
                        'lat': float(point['latitude']),
                        'lng': float(point['longitude'])
                    }
                    for point in polygon_points
                ]
        
        return jsonify({
            'success': True,
            'data': zones
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@shared_bp.route('/zones/by-location', methods=['GET'])
@token_required
def get_zone_by_location():
    """Find zone by coordinates"""
    try:
        # Get query parameters
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        
        if latitude is None or longitude is None:
            return jsonify({'success': False, 'error': 'latitude and longitude are required'}), 400
        
        with db_connection.get_cursor() as cursor:
            # Find zone containing the point using PostGIS-like logic
            # For simplicity, we'll use a basic point-in-polygon check
            cursor.execute("""
                SELECT DISTINCT z.id, z.name, z.cleanliness_score, z.color
                FROM zones z
                JOIN zone_polygons zp ON z.id = zp.zone_id
                WHERE z.is_active = true
                GROUP BY z.id, z.name, z.cleanliness_score, z.color
                HAVING COUNT(zp.id) >= 3
                LIMIT 1
            """)
            zone = cursor.fetchone()
            
            if not zone:
                return jsonify({'success': False, 'error': 'No zone found for this location'}), 404
        
        return jsonify({
            'success': True,
            'data': zone
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@shared_bp.route('/zones/<zone_id>/stats', methods=['GET'])
@token_required
def get_zone_statistics(zone_id):
    """Get detailed statistics for a specific zone"""
    try:
        with db_connection.get_cursor() as cursor:
            # Get zone with statistics
            cursor.execute("""
                SELECT 
                    z.id, z.name, z.cleanliness_score,
                    (SELECT COUNT(*) FROM reports WHERE zone_id = z.id) as total_reports,
                    (SELECT COUNT(*) FROM reports WHERE zone_id = z.id AND status = 'SUBMITTED') as pending_reports,
                    (SELECT COUNT(*) FROM reports WHERE zone_id = z.id AND status = 'COMPLETED') as completed_reports,
                    (SELECT COUNT(*) FROM tasks WHERE zone_id = z.id AND status IN ('APPROVED', 'IN_PROGRESS')) as active_tasks,
                    (SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/86400) 
                     FROM reports WHERE zone_id = z.id AND status = 'COMPLETED') as avg_completion_days
                FROM zones z
                WHERE z.id = %s AND z.is_active = true
            """, (zone_id,))
            zone = cursor.fetchone()
            
            if not zone:
                return jsonify({'success': False, 'error': 'Zone not found'}), 404
            
            # Get recent reports
            cursor.execute("""
                SELECT 
                    r.id, r.description, r.severity, r.status, r.created_at
                FROM reports r
                WHERE r.zone_id = %s
                ORDER BY r.created_at DESC
                LIMIT 5
            """, (zone_id,))
            recent_reports = cursor.fetchall()
            
            # Convert timestamps
            for report in recent_reports:
                report['created_at'] = report['created_at'].isoformat()
        
        response_data = {
            'zone_id': zone['id'],
            'zone_name': zone['name'],
            'cleanliness_score': zone['cleanliness_score'],
            'total_reports': zone['total_reports'],
            'pending_reports': zone['pending_reports'],
            'completed_reports': zone['completed_reports'],
            'active_tasks': zone['active_tasks'],
            'avg_completion_time': f"{zone['avg_completion_days']:.1f} days" if zone['avg_completion_days'] else "N/A",
            'recent_reports': recent_reports
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@shared_bp.route('/reports/<report_id>', methods=['GET'])
@token_required
def get_report_details(report_id):
    """Get detailed report information (accessible by report owner, assigned cleaner, or admin)"""
    try:
        user_id = request.current_user['id']
        user_role = request.current_user['role']
        
        with db_connection.get_cursor() as cursor:
            # Get report with access control
            if user_role == 'ADMIN':
                # Admin can see all reports
                access_condition = "1=1"
                access_params = []
            else:
                # Citizens can see their own reports, cleaners can see assigned reports
                access_condition = "(r.user_id = %s OR r.cleaner_id = %s)"
                access_params = [user_id, user_id]
            
            cursor.execute(f"""
                SELECT 
                    r.*,
                    z.name as zone_name, z.cleanliness_score,
                    reporter.name as reporter_name, reporter.avatar_url as reporter_avatar,
                    cleaner.name as cleaner_name, cleaner.avatar_url as cleaner_avatar,
                    cp.rating as cleaner_rating,
                    wa.description as ai_description, wa.estimated_volume, 
                    wa.environmental_impact, wa.health_hazard, wa.recommended_action,
                    cc.completion_percentage, cc.quality_rating, cc.environmental_benefit,
                    cr.rating as citizen_rating, cr.comment as citizen_comment, cr.created_at as review_date
                FROM reports r
                JOIN zones z ON r.zone_id = z.id
                JOIN users reporter ON r.user_id = reporter.id
                LEFT JOIN users cleaner ON r.cleaner_id = cleaner.id
                LEFT JOIN cleaner_profiles cp ON r.cleaner_id = cp.user_id
                LEFT JOIN waste_analyses wa ON r.id = wa.report_id
                LEFT JOIN cleanup_comparisons cc ON r.id = cc.report_id
                LEFT JOIN cleanup_reviews cr ON r.id = cr.report_id
                WHERE r.id = %s AND {access_condition}
            """, [report_id] + access_params)
            report = cursor.fetchone()
            
            if not report:
                return jsonify({'success': False, 'error': 'Report not found or access denied'}), 404
            
            # Get waste composition if available
            waste_composition = []
            if report.get('ai_description'):
                cursor.execute("""
                    SELECT waste_type, percentage, recyclable
                    FROM waste_compositions wc
                    JOIN waste_analyses wa ON wc.waste_analysis_id = wa.id
                    WHERE wa.report_id = %s
                """, (report_id,))
                waste_composition = cursor.fetchall()
            
            # Get task info if exists
            task_info = None
            cursor.execute("""
                SELECT id, reward, due_date, taken_at, completed_at
                FROM tasks WHERE report_id = %s
            """, (report_id,))
            task = cursor.fetchone()
            
            if task:
                task_info = {
                    'id': task['id'],
                    'reward': float(task['reward']),
                    'due_date': task['due_date'].isoformat(),
                    'taken_at': task['taken_at'].isoformat() if task['taken_at'] else None,
                    'completed_at': task['completed_at'].isoformat() if task['completed_at'] else None
                }
        
        # Structure the response
        response_data = {
            'report': {
                'id': report['id'],
                'description': report['description'],
                'severity': report['severity'],
                'status': report['status'],
                'image_url': report['image_url'],
                'after_image_url': report['after_image_url'],
                'latitude': float(report['latitude']) if report['latitude'] else None,
                'longitude': float(report['longitude']) if report['longitude'] else None,
                'created_at': report['created_at'].isoformat(),
                'completed_at': report['completed_at'].isoformat() if report['completed_at'] else None,
                'decline_reason': report['decline_reason']
            },
            'reporter': {
                'name': report['reporter_name'],
                'avatar_url': report['reporter_avatar']
            },
            'zone': {
                'name': report['zone_name'],
                'cleanliness_score': report['cleanliness_score']
            }
        }
        
        if report['cleaner_name']:
            response_data['cleaner'] = {
                'name': report['cleaner_name'],
                'avatar_url': report['cleaner_avatar'],
                'rating': float(report['cleaner_rating']) if report['cleaner_rating'] else None
            }
        
        if report['ai_description']:
            response_data['ai_analysis'] = {
                'description': report['ai_description'],
                'estimated_volume': report['estimated_volume'],
                'environmental_impact': report['environmental_impact'],
                'health_hazard': report['health_hazard'],
                'recommended_action': report['recommended_action'],
                'waste_composition': waste_composition
            }
        
        if report['completion_percentage']:
            response_data['cleanup_comparison'] = {
                'completion_percentage': report['completion_percentage'],
                'quality_rating': report['quality_rating'],
                'environmental_benefit': report['environmental_benefit']
            }
        
        if report['citizen_rating']:
            response_data['review'] = {
                'rating': report['citizen_rating'],
                'comment': report['citizen_comment'],
                'created_at': report['review_date'].isoformat()
            }
        
        if task_info:
            response_data['task'] = task_info
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@shared_bp.route('/tasks/<task_id>', methods=['GET'])
@token_required
def get_task_details(task_id):
    """Get detailed task information (accessible by task owner or admin)"""
    try:
        user_id = request.current_user['id']
        user_role = request.current_user['role']
        
        with db_connection.get_cursor() as cursor:
            # Get task with access control
            if user_role == 'ADMIN':
                # Admin can see all tasks
                access_condition = "1=1"
                access_params = []
            else:
                # Only assigned cleaner can see the task
                access_condition = "t.cleaner_id = %s"
                access_params = [user_id]
            
            cursor.execute(f"""
                SELECT 
                    t.*,
                    z.name as zone_name, z.cleanliness_score,
                    r.id as report_id, r.description as report_description, 
                    r.image_url as report_image, r.after_image_url,
                    reporter.name as reporter_name,
                    cleaner.name as cleaner_name, cleaner.avatar_url as cleaner_avatar,
                    wa.estimated_volume, wa.environmental_impact, wa.recommended_action,
                    cr.rating as review_rating, cr.comment as review_comment, cr.created_at as review_date,
                    et.amount as earnings_amount, et.status as earnings_status, et.paid_at
                FROM tasks t
                JOIN zones z ON t.zone_id = z.id
                LEFT JOIN reports r ON t.report_id = r.id
                LEFT JOIN users reporter ON r.user_id = reporter.id
                LEFT JOIN users cleaner ON t.cleaner_id = cleaner.id
                LEFT JOIN waste_analyses wa ON r.id = wa.report_id
                LEFT JOIN cleanup_reviews cr ON r.id = cr.report_id
                LEFT JOIN earnings_transactions et ON t.id = et.task_id
                WHERE t.id = %s AND {access_condition}
            """, [task_id] + access_params)
            task = cursor.fetchone()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found or access denied'}), 404
            
            # Get special equipment if available
            special_equipment = []
            if task['report_id']:
                cursor.execute("""
                    SELECT se.equipment_name
                    FROM special_equipment se
                    JOIN waste_analyses wa ON se.waste_analysis_id = wa.id
                    WHERE wa.report_id = %s
                """, (task['report_id'],))
                equipment = cursor.fetchall()
                special_equipment = [eq['equipment_name'] for eq in equipment]
        
        # Structure the response
        response_data = {
            'task': {
                'id': task['id'],
                'description': task['description'],
                'priority': task['priority'],
                'status': task['status'],
                'reward': float(task['reward']),
                'due_date': task['due_date'].isoformat(),
                'created_at': task['created_at'].isoformat(),
                'taken_at': task['taken_at'].isoformat() if task['taken_at'] else None,
                'completed_at': task['completed_at'].isoformat() if task['completed_at'] else None,
                'evidence_image_url': task['evidence_image_url']
            },
            'zone': {
                'name': task['zone_name'],
                'cleanliness_score': task['cleanliness_score']
            }
        }
        
        if task['cleaner_name']:
            response_data['cleaner'] = {
                'name': task['cleaner_name'],
                'avatar_url': task['cleaner_avatar']
            }
        
        if task['report_id']:
            response_data['report'] = {
                'id': task['report_id'],
                'description': task['report_description'],
                'image_url': task['report_image'],
                'after_image_url': task['after_image_url'],
                'reporter_name': task['reporter_name']
            }
            
            if task['estimated_volume']:
                response_data['ai_analysis'] = {
                    'estimated_volume': task['estimated_volume'],
                    'environmental_impact': task['environmental_impact'],
                    'recommended_action': task['recommended_action'],
                    'special_equipment': special_equipment
                }
        
        if task['review_rating']:
            response_data['review'] = {
                'rating': task['review_rating'],
                'comment': task['review_comment'],
                'created_at': task['review_date'].isoformat()
            }
        
        if task['earnings_amount']:
            response_data['earnings'] = {
                'amount': float(task['earnings_amount']),
                'status': task['earnings_status'],
                'paid_at': task['paid_at'].isoformat() if task['paid_at'] else None
            }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500