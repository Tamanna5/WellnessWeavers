"""
Therapy Tools Routes for WellnessWeavers
CBT, behavioral activation, and other evidence-based therapy tools
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import json

from models.thought_record import ThoughtRecord
from models.relapse_prevention import RelapsePrevention
from models.behavioral_activation import BehavioralActivation
from services.cognitive_distortion_detector import cognitive_distortion_detector
from services.seasonal_tracker import seasonal_tracker
from database import db

therapy_tools_bp = Blueprint('therapy_tools', __name__)

# Thought Records Routes
@therapy_tools_bp.route('/thought-records')
@login_required
def thought_records():
    """View thought records interface"""
    # Get user's recent thought records
    recent_records = ThoughtRecord.query.filter_by(user_id=current_user.id)\
                                       .order_by(ThoughtRecord.created_at.desc())\
                                       .limit(10).all()
    
    # Get progress statistics
    progress = ThoughtRecord.get_user_progress(current_user.id)
    
    return render_template('therapy_tools/thought_records.html',
                         recent_records=recent_records,
                         progress=progress)

@therapy_tools_bp.route('/thought-records/new', methods=['GET', 'POST'])
@login_required
def new_thought_record():
    """Create new thought record"""
    if request.method == 'POST':
        try:
            # Get form data
            situation = request.form.get('situation', '').strip()
            primary_emotion = request.form.get('primary_emotion', '').strip()
            emotion_intensity = int(request.form.get('emotion_intensity', 5))
            automatic_thought = request.form.get('automatic_thought', '').strip()
            thought_credibility = int(request.form.get('thought_credibility', 50))
            
            # Create thought record
            thought_record = ThoughtRecord(
                user_id=current_user.id,
                situation=situation,
                primary_emotion=primary_emotion,
                emotion_intensity=emotion_intensity,
                automatic_thought=automatic_thought,
                thought_credibility=thought_credibility,
                date_occurred=date.today()
            )
            
            # Analyze for cognitive distortions
            analysis = cognitive_distortion_detector.analyze_text(automatic_thought)
            if analysis['distortions']:
                thought_record.thought_type = analysis['distortions'][0]['type']
            
            db.session.add(thought_record)
            db.session.commit()
            
            flash('Thought record created successfully!', 'success')
            return redirect(url_for('therapy_tools.thought_records'))
            
        except Exception as e:
            flash(f'Error creating thought record: {str(e)}', 'error')
    
    return render_template('therapy_tools/new_thought_record.html')

@therapy_tools_bp.route('/thought-records/<int:record_id>/complete', methods=['POST'])
@login_required
def complete_thought_record(record_id):
    """Complete a thought record"""
    record = ThoughtRecord.query.get_or_404(record_id)
    
    if record.user_id != current_user.id:
        flash('You can only complete your own thought records.', 'error')
        return redirect(url_for('therapy_tools.thought_records'))
    
    try:
        # Get completion data
        evidence_for = request.form.get('evidence_for_thought', '').strip()
        evidence_against = request.form.get('evidence_against_thought', '').strip()
        alternative_thought = request.form.get('alternative_thought', '').strip()
        alternative_credibility = int(request.form.get('alternative_credibility', 50))
        emotion_after = int(request.form.get('emotion_after', 5))
        helpfulness_rating = int(request.form.get('helpfulness_rating', 5))
        insights = request.form.get('insights_gained', '').strip()
        
        # Update record
        record.evidence_for_thought = evidence_for
        record.evidence_against_thought = evidence_against
        record.alternative_thought = alternative_thought
        record.alternative_credibility = alternative_credibility
        record.emotion_after = emotion_after
        record.helpfulness_rating = helpfulness_rating
        record.insights_gained = insights
        
        # Complete the record
        record.complete_record()
        
        db.session.commit()
        
        flash('Thought record completed successfully!', 'success')
        return redirect(url_for('therapy_tools.thought_records'))
        
    except Exception as e:
        flash(f'Error completing thought record: {str(e)}', 'error')
    
    return redirect(url_for('therapy_tools.thought_records'))

# Behavioral Activation Routes
@therapy_tools_bp.route('/behavioral-activation')
@login_required
def behavioral_activation():
    """View behavioral activation interface"""
    # Get user's recent activities
    recent_activities = BehavioralActivation.query.filter_by(user_id=current_user.id)\
                                                  .order_by(BehavioralActivation.scheduled_date.desc())\
                                                  .limit(10).all()
    
    # Get insights
    insights = BehavioralActivation.get_user_insights(current_user.id)
    
    return render_template('therapy_tools/behavioral_activation.html',
                         recent_activities=recent_activities,
                         insights=insights)

@therapy_tools_bp.route('/behavioral-activation/new', methods=['GET', 'POST'])
@login_required
def new_activity():
    """Schedule new activity"""
    if request.method == 'POST':
        try:
            # Get form data
            activity_name = request.form.get('activity_name', '').strip()
            activity_category = request.form.get('activity_category', '').strip()
            activity_description = request.form.get('activity_description', '').strip()
            scheduled_date = datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%d').date()
            scheduled_time = request.form.get('scheduled_time')
            duration_minutes = int(request.form.get('duration_minutes', 30))
            
            # Create activity
            activity = BehavioralActivation(
                user_id=current_user.id,
                activity_name=activity_name,
                activity_category=activity_category,
                activity_description=activity_description,
                scheduled_date=scheduled_date,
                duration_minutes=duration_minutes
            )
            
            if scheduled_time:
                activity.scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            
            db.session.add(activity)
            db.session.commit()
            
            flash('Activity scheduled successfully!', 'success')
            return redirect(url_for('therapy_tools.behavioral_activation'))
            
        except Exception as e:
            flash(f'Error scheduling activity: {str(e)}', 'error')
    
    # Get activity suggestions
    suggestions = BehavioralActivation.suggest_activities(current_user.id)
    
    return render_template('therapy_tools/new_activity.html',
                         suggestions=suggestions)

@therapy_tools_bp.route('/behavioral-activation/<int:activity_id>/complete', methods=['POST'])
@login_required
def complete_activity(activity_id):
    """Complete an activity"""
    activity = BehavioralActivation.query.get_or_404(activity_id)
    
    if activity.user_id != current_user.id:
        flash('You can only complete your own activities.', 'error')
        return redirect(url_for('therapy_tools.behavioral_activation'))
    
    try:
        # Get completion data
        mood_before = int(request.form.get('mood_before', 5))
        mood_after = int(request.form.get('mood_after', 5))
        enjoyment_rating = int(request.form.get('enjoyment_rating', 5))
        mastery_rating = int(request.form.get('mastery_rating', 5))
        difficulty_rating = int(request.form.get('difficulty_rating', 5))
        
        barriers = request.form.getlist('barriers')
        facilitators = request.form.getlist('facilitators')
        coping_strategies = request.form.getlist('coping_strategies')
        
        # Complete activity
        activity.complete_activity(
            mood_before=mood_before,
            mood_after=mood_after,
            enjoyment_rating=enjoyment_rating,
            mastery_rating=mastery_rating,
            difficulty_rating=difficulty_rating,
            barriers=barriers,
            facilitators=facilitators,
            coping_strategies=coping_strategies
        )
        
        flash('Activity completed successfully!', 'success')
        return redirect(url_for('therapy_tools.behavioral_activation'))
        
    except Exception as e:
        flash(f'Error completing activity: {str(e)}', 'error')
    
    return redirect(url_for('therapy_tools.behavioral_activation'))

# Relapse Prevention Routes
@therapy_tools_bp.route('/relapse-prevention')
@login_required
def relapse_prevention():
    """View relapse prevention interface"""
    # Get user's relapse prevention plan
    prevention_plan = RelapsePrevention.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not prevention_plan:
        # Create default plan
        prevention_plan = RelapsePrevention(user_id=current_user.id)
        db.session.add(prevention_plan)
        db.session.commit()
    
    return render_template('therapy_tools/relapse_prevention.html',
                         prevention_plan=prevention_plan)

@therapy_tools_bp.route('/relapse-prevention/update', methods=['POST'])
@login_required
def update_relapse_prevention():
    """Update relapse prevention plan"""
    prevention_plan = RelapsePrevention.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not prevention_plan:
        prevention_plan = RelapsePrevention(user_id=current_user.id)
        db.session.add(prevention_plan)
    
    try:
        # Update warning signs
        warning_signs = request.form.getlist('warning_signs')
        if warning_signs:
            prevention_plan.personal_warning_signs = warning_signs
        
        # Update effective interventions
        interventions = request.form.getlist('interventions')
        if interventions:
            prevention_plan.effective_interventions = interventions
        
        # Update triggers
        triggers = request.form.getlist('triggers')
        trigger_severity = {}
        for trigger in triggers:
            severity = request.form.get(f'trigger_{trigger}_severity', 5)
            trigger_severity[trigger] = int(severity)
        
        if trigger_severity:
            prevention_plan.triggers_map = trigger_severity
        
        # Update support people
        support_people = request.form.getlist('support_people')
        if support_people:
            prevention_plan.support_people = support_people
        
        # Update cultural factors
        family_expectations = request.form.getlist('family_expectations')
        if family_expectations:
            prevention_plan.family_expectations = family_expectations
        
        academic_pressure = request.form.getlist('academic_pressure')
        if academic_pressure:
            prevention_plan.academic_pressure = academic_pressure
        
        db.session.commit()
        
        flash('Relapse prevention plan updated successfully!', 'success')
        return redirect(url_for('therapy_tools.relapse_prevention'))
        
    except Exception as e:
        flash(f'Error updating relapse prevention plan: {str(e)}', 'error')
    
    return redirect(url_for('therapy_tools.relapse_prevention'))

# Seasonal Tracking Routes
@therapy_tools_bp.route('/seasonal-tracking')
@login_required
def seasonal_tracking():
    """View seasonal tracking interface"""
    # Get user's mood data for seasonal analysis
    from models.mood import Mood
    
    mood_data = Mood.query.filter_by(user_id=current_user.id)\
                         .order_by(Mood.created_at.desc())\
                         .limit(365).all()
    
    # Convert to analysis format
    analysis_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in mood_data]
    
    # Analyze seasonal patterns
    seasonal_analysis = seasonal_tracker.analyze_seasonal_patterns(analysis_data)
    
    # Get seasonal insights
    insights = seasonal_tracker.get_seasonal_insights(current_user.id)
    
    return render_template('therapy_tools/seasonal_tracking.html',
                         seasonal_analysis=seasonal_analysis,
                         insights=insights)

# API Routes
@therapy_tools_bp.route('/api/analyze-text', methods=['POST'])
@login_required
def analyze_text():
    """Analyze text for cognitive distortions"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    analysis = cognitive_distortion_detector.analyze_text(text)
    return jsonify(analysis)

@therapy_tools_bp.route('/api/thought-record-progress')
@login_required
def thought_record_progress():
    """Get thought record progress"""
    progress = ThoughtRecord.get_user_progress(current_user.id)
    return jsonify(progress)

@therapy_tools_bp.route('/api/behavioral-activation-insights')
@login_required
def behavioral_activation_insights():
    """Get behavioral activation insights"""
    insights = BehavioralActivation.get_user_insights(current_user.id)
    return jsonify(insights)

@therapy_tools_bp.route('/api/seasonal-patterns')
@login_required
def seasonal_patterns():
    """Get seasonal pattern analysis"""
    from models.mood import Mood
    
    days = request.args.get('days', 365, type=int)
    mood_data = Mood.query.filter_by(user_id=current_user.id)\
                         .order_by(Mood.created_at.desc())\
                         .limit(days).all()
    
    analysis_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in mood_data]
    seasonal_analysis = seasonal_tracker.analyze_seasonal_patterns(analysis_data, days)
    
    return jsonify(seasonal_analysis)

@therapy_tools_bp.route('/api/activity-suggestions')
@login_required
def activity_suggestions():
    """Get activity suggestions"""
    category = request.args.get('category')
    mood_level = request.args.get('mood_level', type=int)
    
    suggestions = BehavioralActivation.suggest_activities(
        current_user.id, 
        category=category, 
        mood_level=mood_level
    )
    
    return jsonify({'suggestions': suggestions})
