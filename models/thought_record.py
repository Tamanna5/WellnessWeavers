"""
Thought Record Model for WellnessWeavers
Core CBT tool for challenging negative thoughts
"""

from database import db
from datetime import datetime
import json

class ThoughtRecord(db.Model):
    """CBT Thought Record - evidence-based cognitive restructuring"""
    __tablename__ = 'thought_records'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Situation and context
    situation = db.Column(db.Text, nullable=False)  # What happened?
    date_occurred = db.Column(db.Date, nullable=False)
    time_occurred = db.Column(db.Time)
    location = db.Column(db.String(100))
    people_present = db.Column(db.JSON)  # Who was there?
    
    # Initial emotional response
    primary_emotion = db.Column(db.String(50), nullable=False)  # sad, angry, anxious, etc.
    emotion_intensity = db.Column(db.Integer, nullable=False)  # 0-100 scale
    secondary_emotions = db.Column(db.JSON)  # Other emotions felt
    physical_sensations = db.Column(db.JSON)  # What they felt in their body
    
    # Automatic thoughts (the core of CBT)
    automatic_thought = db.Column(db.Text, nullable=False)  # The negative thought
    thought_credibility = db.Column(db.Integer)  # How much they believe it (0-100)
    thought_type = db.Column(db.String(50))  # All-or-nothing, mind reading, etc.
    
    # CBT Process - Evidence gathering
    evidence_for_thought = db.Column(db.Text)  # What supports this thought?
    evidence_against_thought = db.Column(db.Text)  # What contradicts it?
    
    # Cognitive restructuring
    alternative_thought = db.Column(db.Text)  # More balanced thought
    alternative_credibility = db.Column(db.Integer)  # How much they believe it (0-100)
    
    # Outcome
    emotion_after = db.Column(db.Integer)  # Emotion intensity after (0-100)
    emotion_change = db.Column(db.Integer)  # Calculated change
    helpfulness_rating = db.Column(db.Integer)  # How helpful was this exercise (1-10)
    
    # Learning and insights
    insights_gained = db.Column(db.Text)  # What did they learn?
    coping_strategies_used = db.Column(db.JSON)  # What helped?
    follow_up_needed = db.Column(db.Boolean, default=False)
    
    # Cultural context (important for Indian users)
    cultural_factors = db.Column(db.JSON)  # Family expectations, social pressure, etc.
    stigma_concerns = db.Column(db.Boolean, default=False)  # Did stigma affect the situation?
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_completed = db.Column(db.Boolean, default=False)
    is_helpful = db.Column(db.Boolean)  # User's assessment
    
    def __init__(self, **kwargs):
        super(ThoughtRecord, self).__init__(**kwargs)
        self.date_occurred = datetime.utcnow().date()
    
    def complete_record(self):
        """Mark the thought record as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        
        # Calculate emotion change
        if self.emotion_after is not None and self.emotion_intensity is not None:
            self.emotion_change = self.emotion_intensity - self.emotion_after
    
    def get_thought_distortions(self):
        """Analyze the automatic thought for cognitive distortions"""
        distortions = []
        thought = self.automatic_thought.lower()
        
        # Common cognitive distortions
        distortion_patterns = {
            'all_or_nothing': ['always', 'never', 'everyone', 'nobody', 'all', 'none'],
            'overgeneralization': ['always', 'never', 'every time', 'all the time'],
            'mental_filter': ['but', 'however', 'except', 'although'],
            'mind_reading': ['they think', 'they believe', 'they feel', 'they know'],
            'fortune_telling': ['will never', 'will always', 'going to', 'about to'],
            'catastrophizing': ['disaster', 'terrible', 'awful', 'horrible', 'worst'],
            'should_statements': ['should', 'must', 'have to', 'ought to'],
            'labeling': ['i am', 'i\'m a', 'they are', 'he is', 'she is'],
            'personalization': ['my fault', 'because of me', 'i caused', 'i made'],
            'emotional_reasoning': ['i feel', 'i sense', 'i know', 'i believe']
        }
        
        for distortion_type, patterns in distortion_patterns.items():
            if any(pattern in thought for pattern in patterns):
                distortions.append(distortion_type)
        
        return distortions
    
    def suggest_alternatives(self):
        """Suggest alternative thoughts based on cognitive distortions"""
        distortions = self.get_thought_distortions()
        suggestions = []
        
        if 'all_or_nothing' in distortions:
            suggestions.append("Try thinking in shades of gray instead of black and white")
        
        if 'overgeneralization' in distortions:
            suggestions.append("Look for exceptions to your general rule")
        
        if 'mind_reading' in distortions:
            suggestions.append("What evidence do you have for what others are thinking?")
        
        if 'fortune_telling' in distortions:
            suggestions.append("You can't predict the future - focus on what you can control")
        
        if 'catastrophizing' in distortions:
            suggestions.append("What's the worst that could realistically happen?")
        
        if 'should_statements' in distortions:
            suggestions.append("Replace 'should' with 'it would be nice if' or 'I prefer'")
        
        return suggestions
    
    def calculate_progress(self):
        """Calculate progress metrics for this thought record"""
        if not self.is_completed:
            return None
        
        progress = {
            'emotion_reduction': self.emotion_change if self.emotion_change else 0,
            'credibility_shift': 0,
            'helpfulness_score': self.helpfulness_rating or 0,
            'distortions_identified': len(self.get_thought_distortions()),
            'completion_time': None
        }
        
        # Calculate credibility shift
        if self.thought_credibility and self.alternative_credibility:
            progress['credibility_shift'] = self.thought_credibility - self.alternative_credibility
        
        # Calculate completion time
        if self.created_at and self.completed_at:
            progress['completion_time'] = (self.completed_at - self.created_at).total_seconds() / 60  # minutes
        
        return progress
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'situation': self.situation,
            'date_occurred': self.date_occurred.isoformat() if self.date_occurred else None,
            'time_occurred': self.time_occurred.isoformat() if self.time_occurred else None,
            'location': self.location,
            'people_present': self.people_present,
            'primary_emotion': self.primary_emotion,
            'emotion_intensity': self.emotion_intensity,
            'secondary_emotions': self.secondary_emotions,
            'physical_sensations': self.physical_sensations,
            'automatic_thought': self.automatic_thought,
            'thought_credibility': self.thought_credibility,
            'thought_type': self.thought_type,
            'evidence_for_thought': self.evidence_for_thought,
            'evidence_against_thought': self.evidence_against_thought,
            'alternative_thought': self.alternative_thought,
            'alternative_credibility': self.alternative_credibility,
            'emotion_after': self.emotion_after,
            'emotion_change': self.emotion_change,
            'helpfulness_rating': self.helpfulness_rating,
            'insights_gained': self.insights_gained,
            'coping_strategies_used': self.coping_strategies_used,
            'cultural_factors': self.cultural_factors,
            'stigma_concerns': self.stigma_concerns,
            'is_completed': self.is_completed,
            'is_helpful': self.is_helpful,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'distortions': self.get_thought_distortions(),
            'suggestions': self.suggest_alternatives(),
            'progress': self.calculate_progress()
        }
    
    @classmethod
    def get_user_progress(cls, user_id, days=30):
        """Get user's thought record progress over time"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        records = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_date,
            cls.is_completed == True
        ).all()
        
        if not records:
            return {
                'total_records': 0,
                'average_emotion_reduction': 0,
                'average_helpfulness': 0,
                'most_common_distortions': [],
                'progress_trend': 'insufficient_data'
            }
        
        # Calculate metrics
        emotion_reductions = [r.emotion_change for r in records if r.emotion_change]
        helpfulness_scores = [r.helpfulness_rating for r in records if r.helpfulness_rating]
        
        # Count distortions
        distortion_counts = {}
        for record in records:
            for distortion in record.get_thought_distortions():
                distortion_counts[distortion] = distortion_counts.get(distortion, 0) + 1
        
        # Sort by frequency
        most_common = sorted(distortion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_records': len(records),
            'average_emotion_reduction': sum(emotion_reductions) / len(emotion_reductions) if emotion_reductions else 0,
            'average_helpfulness': sum(helpfulness_scores) / len(helpfulness_scores) if helpfulness_scores else 0,
            'most_common_distortions': [{'distortion': d, 'count': c} for d, c in most_common],
            'progress_trend': 'improving' if len(records) >= 5 else 'building'
        }
    
    def __repr__(self):
        return f'<ThoughtRecord {self.id}: {self.primary_emotion} - {self.automatic_thought[:50]}...>'
