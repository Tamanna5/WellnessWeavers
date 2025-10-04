"""
Dashboard routes for WellnessWeavers
Handles user dashboard, analytics, and wellness tracking features
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    from models.mood import Mood
    from models.conversation import Conversation
    from models.achievement import Achievement
    
    # Get user's recent data
    recent_moods = Mood.query.filter_by(user_id=current_user.id)\
                            .order_by(Mood.created_at.desc())\
                            .limit(7).all()
    
    recent_conversations = Conversation.query.filter_by(user_id=current_user.id)\
                                           .order_by(Conversation.created_at.desc())\
                                           .limit(5).all()
    
    user_achievements = current_user.achievements
    
    # Calculate wellness stats
    mood_stats = Mood.get_user_mood_stats(current_user.id, days=30)
    conversation_stats = Conversation.get_user_conversation_stats(current_user.id, days=30)
    
    # Check for new achievements
    new_achievements = Achievement.check_and_award_achievements(current_user)
    
    return render_template('dashboard/dashboard.html', 
                         recent_moods=recent_moods,
                         recent_conversations=recent_conversations,
                         user_achievements=user_achievements,
                         mood_stats=mood_stats,
                         conversation_stats=conversation_stats,
                         new_achievements=new_achievements)

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics and insights page"""
    from models.mood import Mood
    from models.conversation import Conversation
    
    # Get mood patterns and insights
    mood_patterns = Mood.get_mood_patterns(current_user.id, days=90)
    mood_stats = Mood.get_user_mood_stats(current_user.id, days=90)
    conversation_stats = Conversation.get_user_conversation_stats(current_user.id, days=90)
    
    # Get weekly data for charts
    weekly_data = []
    for i in range(12):  # Last 12 weeks
        start_date = datetime.now() - timedelta(weeks=i+1)
        end_date = datetime.now() - timedelta(weeks=i)
        
        week_moods = Mood.query.filter(
            Mood.user_id == current_user.id,
            Mood.created_at >= start_date,
            Mood.created_at < end_date
        ).all()
        
        avg_mood = sum(m.mood_score for m in week_moods) / len(week_moods) if week_moods else 0
        weekly_data.append({
            'week': f"Week {12-i}",
            'average_mood': round(avg_mood, 1),
            'entries': len(week_moods)
        })
    
    weekly_data.reverse()
    
    return render_template('dashboard/analytics.html',
                         mood_patterns=mood_patterns,
                         mood_stats=mood_stats,
                         conversation_stats=conversation_stats,
                         weekly_data=weekly_data)

@dashboard_bp.route('/chat')
@login_required
def chat():
    """AI Chat interface"""
    from models.conversation import Conversation
    
    # Get user's active chat sessions
    active_sessions = Conversation.get_user_active_sessions(current_user.id)
    recent_conversations = Conversation.query.filter_by(user_id=current_user.id)\
                                           .order_by(Conversation.created_at.desc())\
                                           .limit(10).all()
    
    return render_template('dashboard/chat.html',
                         active_sessions=active_sessions,
                         recent_conversations=recent_conversations)

@dashboard_bp.route('/voice-journal')
@login_required
def voice_journal():
    """Voice journal interface"""
    from models.mood import Mood
    
    # Get user's voice entries
    voice_entries = Mood.query.filter(
        Mood.user_id == current_user.id,
        Mood.entry_method == 'voice'
    ).order_by(Mood.created_at.desc()).limit(20).all()
    
    return render_template('dashboard/voicejournal.html',
                         voice_entries=voice_entries)

@dashboard_bp.route('/mood/new', methods=['GET', 'POST'])
@login_required
def new_mood_entry():
    """Create new mood entry"""
    if request.method == 'POST':
        from models.mood import Mood
        from flask import current_app
        
        try:
            # Get form data
            mood_score = float(request.form.get('mood_score', 5))
            mood_label = request.form.get('mood_label', 'neutral')
            intensity = int(request.form.get('intensity', 5))
            notes = request.form.get('notes', '')
            activities = request.form.getlist('activities')
            energy_level = request.form.get('energy_level')
            stress_level = request.form.get('stress_level')
            
            # Create mood entry
            mood = Mood(
                user_id=current_user.id,
                mood_score=mood_score,
                mood_label=mood_label,
                intensity=intensity,
                notes=notes,
                energy_level=int(energy_level) if energy_level else None,
                stress_level=int(stress_level) if stress_level else None,
                language=current_user.preferred_language
            )
            
            mood.set_activities_list(activities)
            
            db = current_app.extensions['sqlalchemy'].db
            db.session.add(mood)
            
            # Update user points and streak
            current_user.add_points(10)  # 10 points for mood entry
            current_user.update_streak()
            
            db.session.commit()
            
            # Check for achievements
            from models.achievement import Achievement
            Achievement.check_and_award_achievements(current_user)
            
            flash('Mood entry recorded successfully!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            flash(f'Error recording mood: {str(e)}', 'error')
    
    return render_template('dashboard/new_mood.html')

@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile and settings"""
    from models.achievement import Achievement
    
    # Get user's achievement progress
    achievement_progress = Achievement.get_user_progress(current_user)
    
    return render_template('dashboard/profile.html',
                         achievement_progress=achievement_progress)

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings and preferences"""
    if request.method == 'POST':
        from flask import current_app
        
        try:
            # Update user preferences
            current_user.preferred_language = request.form.get('preferred_language', 'en')
            current_user.ai_companion_name = request.form.get('ai_companion_name', 'Wellness Buddy')
            current_user.ai_companion_personality = request.form.get('ai_companion_personality', 'supportive_friend')
            
            # Privacy settings
            current_user.data_sharing_consent = 'data_sharing_consent' in request.form
            current_user.analytics_consent = 'analytics_consent' in request.form
            current_user.marketing_consent = 'marketing_consent' in request.form
            
            # Wellness goals
            wellness_goals = request.form.getlist('wellness_goals')
            current_user.set_wellness_goals_list(wellness_goals)
            
            db = current_app.extensions['sqlalchemy'].db
            db.session.commit()
            
            flash('Settings updated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')
    
    return render_template('dashboard/settings.html')

# AJAX endpoints for dashboard
@dashboard_bp.route('/api/mood-chart-data')
@login_required
def mood_chart_data():
    """Get mood data for charts"""
    from models.mood import Mood
    
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    moods = Mood.query.filter(
        Mood.user_id == current_user.id,
        Mood.created_at >= start_date
    ).order_by(Mood.created_at.asc()).all()
    
    chart_data = []
    for mood in moods:
        chart_data.append({
            'date': mood.created_at.strftime('%Y-%m-%d'),
            'mood_score': mood.mood_score,
            'mood_label': mood.mood_label,
            'energy_level': mood.energy_level,
            'stress_level': mood.stress_level
        })
    
    return jsonify(chart_data)

@dashboard_bp.route('/api/quick-mood', methods=['POST'])
@login_required
def quick_mood():
    """Quick mood entry via AJAX"""
    from models.mood import Mood
    from flask import current_app
    
    try:
        data = request.get_json()
        mood_score = data.get('mood_score')
        mood_label = data.get('mood_label')
        
        mood = Mood(
            user_id=current_user.id,
            mood_score=mood_score,
            mood_label=mood_label,
            intensity=5,  # Default
            language=current_user.preferred_language
        )
        
        db = current_app.extensions['sqlalchemy'].db
        db.session.add(mood)
        current_user.add_points(5)  # Quick mood points
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mood recorded!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400