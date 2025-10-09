"""
API Routes for WellnessWeavers
RESTful API endpoints for mobile app and external integrations
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from models import User, Mood, Conversation, Achievement, SupportGroup
from database import db
from services.ai_service import ai_service
from services.crisis_detection import crisis_detection_service
from services.notification_service import notification_service
from utils.data_processor import data_processor

api_bp = Blueprint('api', __name__)

# Authentication decorator for API
def api_auth_required(f):
    """API authentication decorator"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key or user authentication
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Validate API key (implement your API key validation)
            if api_key != current_app.config.get('API_KEY'):
                return jsonify({'error': 'Invalid API key'}), 401
        elif not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# User endpoints
@api_bp.route('/users/profile', methods=['GET', 'PUT'])
@api_auth_required
def user_profile():
    """Get or update user profile"""
    if request.method == 'GET':
        return jsonify(current_user.to_dict(include_sensitive=True))
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['full_name', 'preferred_language', 'cultural_background', 
                         'location_city', 'location_state', 'ai_companion_personality']
        
        for field in allowed_fields:
            if field in data:
                setattr(current_user, field, data[field])
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})

@api_bp.route('/users/wellness-score', methods=['GET'])
@api_auth_required
def user_wellness_score():
    """Get user's current wellness score and insights"""
    # Get recent mood data
    recent_moods = Mood.query.filter_by(user_id=current_user.id)\
                           .order_by(Mood.created_at.desc())\
                           .limit(30).all()
    
    if not recent_moods:
        return jsonify({
            'wellness_score': 50.0,
            'insights': [],
            'message': 'No mood data available'
        })
    
    # Calculate wellness score
    mood_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in recent_moods]
    wellness_score = current_user.wellness_score
    
    # Generate insights
    insights = current_user.get_wellness_insights()
    
    return jsonify({
        'wellness_score': wellness_score,
        'insights': insights,
        'recent_moods': len(recent_moods),
        'streak_days': current_user.streak_days
    })

# Mood endpoints
@api_bp.route('/moods', methods=['GET', 'POST'])
@api_auth_required
def moods():
    """Get or create mood entries"""
    if request.method == 'GET':
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query moods
        moods = Mood.query.filter(
            Mood.user_id == current_user.id,
            Mood.created_at >= start_date
        ).order_by(Mood.created_at.desc()).limit(limit).all()
        
        return jsonify([mood.to_dict() for mood in moods])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['mood_score', 'mood_label']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create mood entry
        mood = Mood(
            user_id=current_user.id,
            mood_score=data['mood_score'],
            mood_label=data['mood_label'],
            intensity=data.get('intensity', 5),
            notes=data.get('notes', ''),
            energy_level=data.get('energy_level'),
            stress_level=data.get('stress_level'),
            language=current_user.preferred_language
        )
        
        # Set activities if provided
        if 'activities' in data:
            mood.set_activities_list(data['activities'])
        
        db.session.add(mood)
        
        # Update user points and streak
        current_user.add_experience_points(10)
        current_user.update_streak()
        
        db.session.commit()
        
        # Check for crisis indicators
        if mood.notes:
            crisis_alert = crisis_detection_service.detect_crisis_in_mood_entry(mood.id)
            if crisis_alert:
                return jsonify({
                    'message': 'Mood entry recorded',
                    'crisis_alert': True,
                    'alert_id': crisis_alert.id
                }), 201
        
        return jsonify({'message': 'Mood entry recorded successfully'}), 201

@api_bp.route('/moods/analytics', methods=['GET'])
@api_auth_required
def mood_analytics():
    """Get mood analytics and insights"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get mood data
    moods = Mood.query.filter(
        Mood.user_id == current_user.id,
        Mood.created_at >= start_date
    ).all()
    
    if not moods:
        return jsonify({'error': 'No mood data available'}), 404
    
    # Process mood data
    mood_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in moods]
    analysis = data_processor.analyze_mood_patterns(mood_data)
    
    # Generate insights
    insights = data_processor.generate_wellness_insights(analysis)
    
    return jsonify({
        'analysis': analysis,
        'insights': insights,
        'wellness_score': current_user.wellness_score
    })

# AI Chat endpoints
@api_bp.route('/chat/message', methods=['POST'])
@api_auth_required
def send_chat_message():
    """Send message to AI companion"""
    data = request.get_json()
    
    if 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    message = data['message']
    session_id = data.get('session_id', f"session_{current_user.id}_{datetime.utcnow().timestamp()}")
    
    # Analyze message for crisis indicators
    crisis_analysis = crisis_detection_service.analyze_text(message)
    
    # Generate AI response
    ai_response = ai_service.generate_response(message)
    
    # Save conversation
    conversation = Conversation(
        user_id=current_user.id,
        session_id=session_id,
        message=message,
        response=ai_response,
        sentiment=crisis_analysis['risk_level'],
        sentiment_score=crisis_analysis['confidence'],
        crisis_indicators=crisis_analysis['indicators']
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    # Check for crisis intervention
    if crisis_analysis['risk_level'] in ['high', 'critical']:
        crisis_alert = crisis_detection_service.detect_crisis_in_conversation(conversation.id)
        return jsonify({
            'response': ai_response,
            'session_id': session_id,
            'crisis_alert': True,
            'alert_id': crisis_alert.id if crisis_alert else None
        })
    
    return jsonify({
        'response': ai_response,
        'session_id': session_id,
        'crisis_alert': False
    })

@api_bp.route('/chat/sessions', methods=['GET'])
@api_auth_required
def get_chat_sessions():
    """Get user's chat sessions"""
    sessions = Conversation.get_user_active_sessions(current_user.id)
    
    session_list = []
    for session_id, conversations in sessions.items():
        session_list.append({
            'session_id': session_id,
            'message_count': len(conversations),
            'last_message': conversations[0].created_at.isoformat() if conversations else None
        })
    
    return jsonify(session_list)

# Achievement endpoints
@api_bp.route('/achievements', methods=['GET'])
@api_auth_required
def get_achievements():
    """Get user's achievements"""
    progress = Achievement.get_user_progress(current_user)
    return jsonify(progress)

@api_bp.route('/achievements/check', methods=['POST'])
@api_auth_required
def check_achievements():
    """Check and award new achievements"""
    new_achievements = Achievement.check_and_award_achievements(current_user)
    
    return jsonify({
        'new_achievements': [achievement.to_dict() for achievement in new_achievements],
        'total_achievements': len(new_achievements)
    })

# Community endpoints
@api_bp.route('/groups', methods=['GET'])
@api_auth_required
def get_groups():
    """Get support groups"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = SupportGroup.query.filter(
        SupportGroup.is_public == True,
        SupportGroup.status == 'active'
    )
    
    if category != 'all':
        query = query.filter(SupportGroup.category == category)
    
    if search:
        query = query.filter(
            SupportGroup.name.contains(search) |
            SupportGroup.description.contains(search)
        )
    
    groups = query.paginate(page=page, per_page=20, error_out=False)
    
    return jsonify({
        'groups': [group.to_dict() for group in groups.items],
        'total': groups.total,
        'pages': groups.pages,
        'current_page': page
    })

@api_bp.route('/groups/<int:group_id>/join', methods=['POST'])
@api_auth_required
def join_group(group_id):
    """Join a support group"""
    group = SupportGroup.query.get_or_404(group_id)
    
    # Check if already a member
    from models.community import GroupMembership
    existing_membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if existing_membership:
        if existing_membership.status == 'active':
            return jsonify({'message': 'Already a member'}), 400
        else:
            return jsonify({'message': 'Membership request pending'}), 400
    
    # Create new membership
    membership = GroupMembership(
        user_id=current_user.id,
        group_id=group_id,
        status='active' if group.is_public else 'pending',
        joined_at=datetime.utcnow()
    )
    
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({'message': 'Successfully joined group'})

# Crisis endpoints
@api_bp.route('/crisis/check', methods=['POST'])
@api_auth_required
def check_crisis():
    """Check for crisis indicators in text"""
    data = request.get_json()
    
    if 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400
    
    analysis = crisis_detection_service.analyze_text(data['text'])
    
    return jsonify(analysis)

@api_bp.route('/crisis/history', methods=['GET'])
@api_auth_required
def get_crisis_history():
    """Get user's crisis history"""
    days = request.args.get('days', 30, type=int)
    history = crisis_detection_service.get_user_crisis_history(current_user.id, days)
    
    return jsonify(history)

# Notification endpoints
@api_bp.route('/notifications/preferences', methods=['GET', 'PUT'])
@api_auth_required
def notification_preferences():
    """Get or update notification preferences"""
    if request.method == 'GET':
        return jsonify({
            'email_notifications': current_user.email_notifications,
            'sms_notifications': current_user.sms_notifications,
            'push_notifications': current_user.push_notifications
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        if 'email_notifications' in data:
            current_user.email_notifications = data['email_notifications']
        if 'sms_notifications' in data:
            current_user.sms_notifications = data['sms_notifications']
        if 'push_notifications' in data:
            current_user.push_notifications = data['push_notifications']
        
        db.session.commit()
        return jsonify({'message': 'Preferences updated successfully'})

# Analytics endpoints
@api_bp.route('/analytics/insights', methods=['GET'])
@api_auth_required
def get_analytics_insights():
    """Get comprehensive analytics insights"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get mood data
    moods = Mood.query.filter(
        Mood.user_id == current_user.id,
        Mood.created_at >= start_date
    ).all()
    
    if not moods:
        return jsonify({'error': 'No data available'}), 404
    
    # Process data
    mood_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in moods]
    analysis = data_processor.analyze_mood_patterns(mood_data)
    insights = data_processor.generate_wellness_insights(analysis)
    
    # Get crisis statistics
    crisis_stats = crisis_detection_service.get_crisis_statistics(current_user.id)
    
    return jsonify({
        'mood_analysis': analysis,
        'insights': insights,
        'crisis_statistics': crisis_stats,
        'wellness_score': current_user.wellness_score,
        'user_stats': {
            'total_points': current_user.total_points,
            'level': current_user.level,
            'streak_days': current_user.streak_days
        }
    })

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def api_health():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'database': 'connected',
            'ai_service': 'available',
            'crisis_detection': 'active'
        }
    })

# Error handlers
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
