"""
Mood Model for WellnessWeavers
Comprehensive mood tracking with AI analysis and pattern recognition
"""

from app import db
from datetime import datetime
import json

class Mood(db.Model):
    """Enhanced Mood model with comprehensive tracking and AI analysis"""
    __tablename__ = 'moods'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic mood data
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    emotion = db.Column(db.String(50))  # Primary emotion (emoji or text)
    secondary_emotions = db.Column(db.JSON)  # Additional emotions detected
    intensity = db.Column(db.Integer, default=5)  # 1-10, how intense the feeling is
    
    # User input
    notes = db.Column(db.Text)  # User's written description
    activities = db.Column(db.JSON)  # List of activities done recently
    social_context = db.Column(db.JSON)  # Who they were with
    
    # Environmental context
    weather = db.Column(db.String(50))
    location = db.Column(db.String(100))
    time_of_day = db.Column(db.String(20))  # morning, afternoon, evening, night
    
    # Physical factors
    sleep_hours = db.Column(db.Float)  # Hours slept last night
    energy_level = db.Column(db.Integer)  # 1-10 physical energy
    physical_symptoms = db.Column(db.JSON)  # List of physical symptoms
    
    # Mental health specific
    anxiety_level = db.Column(db.Integer)  # 1-10 anxiety rating
    stress_level = db.Column(db.Integer)  # 1-10 stress rating
    motivation_level = db.Column(db.Integer)  # 1-10 motivation
    focus_level = db.Column(db.Integer)  # 1-10 ability to concentrate
    
    # AI Analysis results
    sentiment_score = db.Column(db.Float)  # -1.0 to 1.0 from text analysis
    detected_emotions = db.Column(db.JSON)  # Multiple emotions from AI
    confidence_score = db.Column(db.Float)  # AI confidence in analysis
    language_detected = db.Column(db.String(10))  # Language of notes
    
    # Risk assessment
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    risk_factors = db.Column(db.JSON)  # Specific risk indicators found
    intervention_suggested = db.Column(db.Boolean, default=False)
    
    # Triggers and patterns
    identified_triggers = db.Column(db.JSON)  # Triggers mentioned or detected
    coping_strategies_used = db.Column(db.JSON)  # What user did to cope
    effectiveness_rating = db.Column(db.Integer)  # How well coping worked (1-10)
    
    # Correlation tracking
    medication_taken = db.Column(db.Boolean)  # Did user take meds today
    therapy_session_nearby = db.Column(db.Boolean)  # Therapy within 24h
    menstrual_cycle_day = db.Column(db.Integer)  # For menstrual tracking
    
    # Metadata
    entry_method = db.Column(db.String(20), default='manual')  # manual, voice, quick
    processing_time = db.Column(db.Float)  # Time taken for AI analysis
    version = db.Column(db.String(10), default='1.0')  # Data schema version
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    analyzed_at = db.Column(db.DateTime)  # When AI analysis was completed
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='moods')
    
    def analyze_with_ai(self, ai_service):
        """Analyze mood entry with AI services"""
        if not self.notes:
            return
        
        try:
            # Sentiment analysis
            sentiment_data = ai_service.analyze_sentiment(self.notes)
            self.sentiment_score = sentiment_data.get('score', 0.0)
            self.confidence_score = sentiment_data.get('confidence', 0.0)
            
            # Emotion detection
            emotions = ai_service.detect_emotions(self.notes)
            self.detected_emotions = emotions
            
            # Language detection
            self.language_detected = ai_service.detect_language(self.notes)
            
            # Risk assessment
            risk_data = ai_service.assess_risk(self.notes)
            self.risk_level = risk_data.get('level', 'low')
            self.risk_factors = risk_data.get('factors', [])
            
            # Trigger identification
            self.identified_triggers = ai_service.identify_triggers(self.notes)
            
            # Mark as analyzed
            self.analyzed_at = datetime.utcnow()
            
        except Exception as e:
            # Log error but don't fail the mood entry
            print(f"AI analysis failed for mood {self.id}: {str(e)}")
    
    def calculate_wellness_impact(self):
        """Calculate how this mood entry impacts overall wellness score"""
        base_impact = self.mood_score - 5  # Neutral is 5, so this gives -4 to +5
        
        # Factor in intensity
        intensity_multiplier = self.intensity / 5  # Scale 1-10 to 0.2-2
        
        # Factor in risk level
        risk_penalties = {
            'low': 0,
            'medium': -2,
            'high': -5,
            'critical': -10
        }
        risk_penalty = risk_penalties.get(self.risk_level, 0)
        
        # Factor in coping strategies
        coping_bonus = 0
        if self.coping_strategies_used and self.effectiveness_rating:
            coping_bonus = (self.effectiveness_rating - 5) * 0.5
        
        final_impact = (base_impact * intensity_multiplier) + risk_penalty + coping_bonus
        return max(-10, min(10, final_impact))  # Clamp between -10 and 10
    
    def get_mood_context(self):
        """Get contextual information about this mood entry"""
        context = {}
        
        # Time context
        if self.time_of_day:
            context['time_of_day'] = self.time_of_day
        
        # Environmental context
        if self.weather or self.location:
            context['environment'] = {
                'weather': self.weather,
                'location': self.location
            }
        
        # Social context
        if self.social_context:
            context['social'] = self.social_context
        
        # Physical context
        physical_factors = {}
        if self.sleep_hours:
            physical_factors['sleep_hours'] = self.sleep_hours
        if self.energy_level:
            physical_factors['energy_level'] = self.energy_level
        if physical_factors:
            context['physical'] = physical_factors
        
        return context
    
    def get_recommendations(self):
        """Generate personalized recommendations based on this mood entry"""
        recommendations = []
        
        # Low mood recommendations
        if self.mood_score <= 3:
            recommendations.extend([
                {
                    'type': 'immediate',
                    'title': 'Reach Out for Support',
                    'description': 'Consider talking to someone you trust or a professional',
                    'action': 'contact_support'
                },
                {
                    'type': 'activity',
                    'title': 'Gentle Movement',
                    'description': 'Try a short walk or gentle stretching',
                    'action': 'suggest_activity'
                }
            ])
        
        # High anxiety recommendations
        if self.anxiety_level and self.anxiety_level >= 7:
            recommendations.append({
                'type': 'coping',
                'title': 'Breathing Exercise',
                'description': '4-7-8 breathing can help reduce anxiety',
                'action': 'breathing_exercise'
            })
        
        # Low energy recommendations
        if self.energy_level and self.energy_level <= 3:
            if self.sleep_hours and self.sleep_hours < 6:
                recommendations.append({
                    'type': 'lifestyle',
                    'title': 'Prioritize Sleep',
                    'description': 'You\'ve been getting less sleep. Consider an earlier bedtime',
                    'action': 'sleep_hygiene'
                })
        
        # Trigger-based recommendations
        if self.identified_triggers:
            recommendations.append({
                'type': 'pattern',
                'title': 'Trigger Awareness',
                'description': f'Noticed triggers: {", ".join(self.identified_triggers[:3])}',
                'action': 'explore_triggers'
            })
        
        return recommendations
    
    def to_dict(self, include_analysis=False):
        """Convert mood entry to dictionary"""
        mood_dict = {
            'id': self.id,
            'mood_score': self.mood_score,
            'emotion': self.emotion,
            'notes': self.notes,
            'activities': self.activities,
            'intensity': self.intensity,
            'anxiety_level': self.anxiety_level,
            'stress_level': self.stress_level,
            'energy_level': self.energy_level,
            'sleep_hours': self.sleep_hours,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'entry_method': self.entry_method
        }
        
        if include_analysis:
            mood_dict.update({
                'sentiment_score': self.sentiment_score,
                'detected_emotions': self.detected_emotions,
                'risk_level': self.risk_level,
                'identified_triggers': self.identified_triggers,
                'coping_strategies_used': self.coping_strategies_used,
                'effectiveness_rating': self.effectiveness_rating,
                'recommendations': self.get_recommendations()
            })
        
        return mood_dict
    
    @classmethod
    def get_mood_trends(cls, user_id, days=30):
        """Analyze mood trends for a user over specified days"""
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        moods = cls.query.filter(
            cls.user_id == user_id,
            cls.timestamp >= start_date
        ).order_by(cls.timestamp.asc()).all()
        
        if not moods:
            return None
        
        # Calculate basic statistics
        mood_scores = [m.mood_score for m in moods]
        avg_mood = sum(mood_scores) / len(mood_scores)
        
        # Identify patterns
        trends = {
            'average_mood': avg_mood,
            'total_entries': len(moods),
            'mood_range': {
                'min': min(mood_scores),
                'max': max(mood_scores)
            },
            'trend_direction': cls._calculate_trend_direction(moods),
            'most_common_emotions': cls._get_common_emotions(moods),
            'risk_distribution': cls._get_risk_distribution(moods),
            'best_day_time': cls._get_best_time_of_day(moods),
            'correlation_insights': cls._get_correlation_insights(moods)
        }
        
        return trends
    
    @staticmethod
    def _calculate_trend_direction(moods):
        """Calculate if mood is trending up, down, or stable"""
        if len(moods) < 5:
            return 'insufficient_data'
        
        recent_avg = sum(m.mood_score for m in moods[-5:]) / 5
        earlier_avg = sum(m.mood_score for m in moods[:5]) / 5
        
        diff = recent_avg - earlier_avg
        
        if diff > 1:
            return 'improving'
        elif diff < -1:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _get_common_emotions(moods):
        """Get most commonly logged emotions"""
        emotion_count = {}
        for mood in moods:
            if mood.emotion:
                emotion_count[mood.emotion] = emotion_count.get(mood.emotion, 0) + 1
        
        return sorted(emotion_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    @staticmethod
    def _get_risk_distribution(moods):
        """Get distribution of risk levels"""
        risk_count = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for mood in moods:
            risk_count[mood.risk_level] = risk_count.get(mood.risk_level, 0) + 1
        
        return risk_count
    
    @staticmethod
    def _get_best_time_of_day(moods):
        """Find the time of day with best mood scores"""
        time_scores = {}
        time_counts = {}
        
        for mood in moods:
            if mood.time_of_day:
                time_scores[mood.time_of_day] = time_scores.get(mood.time_of_day, 0) + mood.mood_score
                time_counts[mood.time_of_day] = time_counts.get(mood.time_of_day, 0) + 1
        
        if not time_scores:
            return None
        
        # Calculate averages
        time_averages = {
            time: scores / time_counts[time] 
            for time, scores in time_scores.items()
        }
        
        return max(time_averages.items(), key=lambda x: x[1])
    
    @staticmethod
    def _get_correlation_insights(moods):
        """Generate correlation insights"""
        insights = []
        
        # Sleep correlation
        sleep_moods = [(m.sleep_hours, m.mood_score) for m in moods if m.sleep_hours]
        if len(sleep_moods) > 5:
            import numpy as np
            sleep_hours, mood_scores = zip(*sleep_moods)
            correlation = np.corrcoef(sleep_hours, mood_scores)[0, 1]
            
            if correlation > 0.3:
                insights.append({
                    'type': 'sleep',
                    'message': 'Better sleep correlates with better mood',
                    'correlation': correlation
                })
            elif correlation < -0.3:
                insights.append({
                    'type': 'sleep',
                    'message': 'Sleep issues may be affecting your mood',
                    'correlation': correlation
                })
        
        return insights
    
    def __repr__(self):
        return f'<Mood {self.id}: {self.mood_score}/10 at {self.timestamp}>'


class MoodPattern(db.Model):
    """Identified mood patterns for users"""
    __tablename__ = 'mood_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    pattern_type = db.Column(db.String(50), nullable=False)  # weekly, seasonal, event-based, cyclical
    pattern_name = db.Column(db.String(100))  # Descriptive name
    description = db.Column(db.Text)  # Detailed description
    
    # Pattern details
    triggers = db.Column(db.JSON)  # What triggers this pattern
    duration_days = db.Column(db.Integer)  # How long pattern lasts
    frequency = db.Column(db.String(50))  # How often it occurs
    intensity = db.Column(db.String(20))  # mild, moderate, severe
    
    # Pattern characteristics
    mood_range = db.Column(db.JSON)  # Typical mood range during pattern
    common_emotions = db.Column(db.JSON)  # Emotions commonly felt
    physical_symptoms = db.Column(db.JSON)  # Associated physical symptoms
    
    # Detection metadata
    confidence_score = db.Column(db.Float)  # AI confidence in pattern
    occurrences_count = db.Column(db.Integer, default=1)  # How many times detected
    accuracy_rating = db.Column(db.Float)  # User feedback on accuracy
    
    # Intervention recommendations
    suggested_interventions = db.Column(db.JSON)
    successful_coping_strategies = db.Column(db.JSON)
    
    # Timestamps
    first_detected = db.Column(db.DateTime, default=datetime.utcnow)
    last_occurrence = db.Column(db.DateTime)
    next_predicted = db.Column(db.DateTime)  # When pattern might occur again
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    user_confirmed = db.Column(db.Boolean)  # User acknowledged pattern
    
    def to_dict(self):
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'pattern_name': self.pattern_name,
            'description': self.description,
            'triggers': self.triggers,
            'duration_days': self.duration_days,
            'frequency': self.frequency,
            'confidence_score': self.confidence_score,
            'suggested_interventions': self.suggested_interventions,
            'next_predicted': self.next_predicted.isoformat() if self.next_predicted else None
        }
    
    def __repr__(self):
        return f'<MoodPattern {self.pattern_name}: {self.pattern_type}>'