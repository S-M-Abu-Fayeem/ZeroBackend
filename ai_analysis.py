from flask import Blueprint, jsonify, request
from auth import token_required
from models import db_connection
from ai_service import ai_service

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai/test-vision', methods=['POST'])
def test_vision():
    """Test vision analysis with a sample image"""
    try:
        data = request.get_json()
        image_url = data.get('image_url', 'https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=500')
        
        print(f"🧪 Testing vision with: {image_url}")
        
        # Test the vision analysis directly
        result = ai_service._analyze_image_with_free_vision(image_url)
        
        return jsonify({
            'success': True,
            'vision_result': result,
            'config': {
                'use_free_vision': ai_service.use_free_vision,
                'has_hf_token': bool(ai_service.hf_token and ai_service.hf_token != 'your_hf_token_here')
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/analyze-waste', methods=['POST'])
@token_required
def analyze_waste_image():
    """Submit image for AI waste analysis"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_url'):
            return jsonify({'success': False, 'error': 'image_url is required'}), 400
        
        # Use real AI analysis service
        analysis_result = ai_service.analyze_waste_image(data['image_url'])
        
        return jsonify({
            'success': True,
            'data': analysis_result
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/compare-cleanup', methods=['POST'])
@token_required
def compare_cleanup_images():
    """Compare before and after cleanup images"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['before_image_url', 'after_image_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Use real AI comparison service
        comparison_result = ai_service.compare_cleanup_images(
            data['before_image_url'], 
            data['after_image_url']
        )
        
        # If report_id is provided, save the comparison to database
        if data.get('report_id'):
            user_id = request.current_user['id']
            
            with db_connection.get_cursor(commit=True) as cursor:
                # Save cleanup comparison
                cursor.execute("""
                    INSERT INTO cleanup_comparisons 
                    (report_id, completion_percentage, before_summary, after_summary, 
                     quality_rating, environmental_benefit, verification_status, feedback, confidence, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['report_id'], comparison_result['completionPercentage'],
                    comparison_result['beforeSummary'], comparison_result['afterSummary'],
                    comparison_result['qualityRating'], comparison_result['environmentalBenefit'],
                    comparison_result['verificationStatus'], comparison_result['feedback'],
                    comparison_result['confidence'], user_id
                ))
                comparison = cursor.fetchone()
                
                # Save waste removed breakdown
                for waste in comparison_result['wasteRemoved']:
                    cursor.execute("""
                        INSERT INTO cleanup_waste_removed 
                        (cleanup_comparison_id, waste_type, percentage, recyclable)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        comparison['id'], waste['type'], 
                        waste['percentage'], waste['recyclable']
                    ))
        
        return jsonify({
            'success': True,
            'data': comparison_result
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/ai/analyze-report/<report_id>', methods=['POST'])
@token_required
def analyze_existing_report(report_id):
    """Analyze an existing report's image with AI"""
    try:
        user_id = request.current_user['id']
        user_role = request.current_user['role']

        # Phase 1: read/validate report quickly (no long transaction).
        with db_connection.get_cursor() as cursor:
            if user_role == 'ADMIN':
                access_condition = "1=1"
                access_params = []
            else:
                access_condition = "(user_id = %s OR cleaner_id = %s)"
                access_params = [user_id, user_id]

            cursor.execute(f"""
                SELECT id, image_url, severity FROM reports
                WHERE id = %s AND {access_condition}
            """, [report_id] + access_params)
            report = cursor.fetchone()

            if not report:
                return jsonify({'success': False, 'error': 'Report not found or access denied'}), 404

            if not report['image_url']:
                return jsonify({'success': False, 'error': 'Report has no image to analyze'}), 400

            cursor.execute("""
                SELECT id FROM waste_analyses WHERE report_id = %s
            """, (report_id,))
            existing_analysis = cursor.fetchone()

            if existing_analysis:
                return jsonify({'success': False, 'error': 'Report already has AI analysis'}), 409

        # Phase 2: AI network call outside DB cursor.
        analysis_result = ai_service.analyze_waste_image(report['image_url'])

        # Phase 3: persist in short write transaction.
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO waste_analyses
                (report_id, description, severity, estimated_volume, environmental_impact,
                 health_hazard, hazard_details, recommended_action, estimated_cleanup_time,
                 confidence, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                report_id, analysis_result['description'], analysis_result['severity'],
                analysis_result['estimatedVolume'], analysis_result['environmentalImpact'],
                analysis_result['healthHazard'], analysis_result.get('hazardDetails', ''),
                analysis_result['recommendedAction'], analysis_result['estimatedCleanupTime'],
                analysis_result['confidence'], user_id
            ))
            analysis = cursor.fetchone()

            for waste in analysis_result['wasteComposition']:
                cursor.execute("""
                    INSERT INTO waste_compositions
                    (waste_analysis_id, waste_type, percentage, recyclable)
                    VALUES (%s, %s, %s, %s)
                """, (
                    analysis['id'], waste['type'],
                    waste['percentage'], waste['recyclable']
                ))

            for equipment in analysis_result['specialEquipmentNeeded']:
                cursor.execute("""
                    INSERT INTO special_equipment (waste_analysis_id, equipment_name)
                    VALUES (%s, %s)
                """, (analysis['id'], equipment))
        
        return jsonify({
            'success': True,
            'message': 'AI analysis completed and saved',
            'data': analysis_result
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500