"""
Behavioral Activation Model for WellnessWeavers
Evidence-based treatment for depression
"""

from database import db
from datetime import datetime, date, timedelta
import json

class BehavioralActivation(db.Model):
    """Behavioral activation scheduling for depression treatment"""
    __tablename__ = 'behavioral_activation'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Activity categories
    activity_name = db.Column(db.String(100), nullable=False)
    activity_category = db.Column(db.String(50), nullable=False)  # pleasurable, mastery, social, physical
    activity_description = db.Column(db.Text)
    
    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer, default=30)
    
    # Completion tracking
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    actual_duration = db.Column(db.Integer)  # Actual time spent
    
    # Mood tracking
    mood_before = db.Column(db.Integer)  # Mood before activity (1-10)
    mood_after = db.Column(db.Integer)  # Mood after activity (1-10)
    mood_change = db.Column(db.Integer)  # Calculated change
    
    # Enjoyment and mastery
    enjoyment_rating = db.Column(db.Integer)  # How much they enjoyed it (1-10)
    mastery_rating = db.Column(db.Integer)  # How accomplished they felt (1-10)
    difficulty_rating = db.Column(db.Integer)  # How difficult it was (1-10)
    
    # Barriers and facilitators
    barriers_encountered = db.Column(db.JSON)  # What got in the way
    facilitators_used = db.Column(db.JSON)  # What helped
    coping_strategies = db.Column(db.JSON)  # Strategies used
    
    # Cultural and contextual factors
    family_involvement = db.Column(db.Boolean, default=False)  # Did family help/hinder?
    academic_related = db.Column(db.Boolean, default=False)  # Related to studies?
    social_pressure = db.Column(db.Integer)  # Social pressure felt (1-10)
    stigma_concerns = db.Column(db.Boolean, default=False)  # Stigma concerns?
    
    # Follow-up and planning
    repeat_activity = db.Column(db.Boolean, default=False)  # Would they do it again?
    modify_activity = db.Column(db.Text)  # How would they change it?
    next_scheduling = db.Column(db.Date)  # When to schedule next
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def complete_activity(self, mood_before, mood_after, enjoyment_rating, 
                         mastery_rating, difficulty_rating, barriers=None, 
                         facilitators=None, coping_strategies=None):
        """Mark activity as completed with ratings"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.mood_before = mood_before
        self.mood_after = mood_after
        self.mood_change = mood_after - mood_before
        self.enjoyment_rating = enjoyment_rating
        self.mastery_rating = mastery_rating
        self.difficulty_rating = difficulty_rating
        
        if barriers:
            self.barriers_encountered = barriers
        if facilitators:
            self.facilitators_used = facilitators
        if coping_strategies:
            self.coping_strategies = coping_strategies
        
        db.session.commit()
    
    def get_activity_effectiveness(self):
        """Calculate how effective this activity was"""
        if not self.is_completed:
            return None
        
        # Weighted score considering mood change, enjoyment, and mastery
        mood_score = max(0, self.mood_change) * 0.4  # 40% weight on mood improvement
        enjoyment_score = (self.enjoyment_rating or 0) * 0.3  # 30% weight on enjoyment
        mastery_score = (self.mastery_rating or 0) * 0.3  # 30% weight on mastery
        
        effectiveness = mood_score + enjoyment_score + mastery_score
        return min(10, max(0, effectiveness))  # Scale to 0-10
    
    def suggest_modifications(self):
        """Suggest modifications based on barriers and ratings"""
        suggestions = []
        
        if self.difficulty_rating and self.difficulty_rating > 7:
            suggestions.append("Consider breaking this activity into smaller steps")
        
        if self.enjoyment_rating and self.enjoyment_rating < 4:
            suggestions.append("Try a different variation of this activity")
        
        if self.barriers_encountered:
            for barrier in self.barriers_encountered:
                if 'time' in barrier.lower():
                    suggestions.append("Schedule this activity for a different time")
                elif 'energy' in barrier.lower():
                    suggestions.append("Try a shorter version of this activity")
                elif 'motivation' in barrier.lower():
                    suggestions.append("Pair this with something you enjoy")
        
        return suggestions
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'activity_name': self.activity_name,
            'activity_category': self.activity_category,
            'activity_description': self.activity_description,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'duration_minutes': self.duration_minutes,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'actual_duration': self.actual_duration,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after,
            'mood_change': self.mood_change,
            'enjoyment_rating': self.enjoyment_rating,
            'mastery_rating': self.mastery_rating,
            'difficulty_rating': self.difficulty_rating,
            'barriers_encountered': self.barriers_encountered,
            'facilitators_used': self.facilitators_used,
            'coping_strategies': self.coping_strategies,
            'family_involvement': self.family_involvement,
            'academic_related': self.academic_related,
            'social_pressure': self.social_pressure,
            'stigma_concerns': self.stigma_concerns,
            'repeat_activity': self.repeat_activity,
            'modify_activity': self.modify_activity,
            'next_scheduling': self.next_scheduling,
            'effectiveness_score': self.get_activity_effectiveness(),
            'suggestions': self.suggest_modifications(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_user_insights(cls, user_id, days=30):
        """Get behavioral activation insights for user"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        activities = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_date
        ).all()
        
        if not activities:
            return {
                'total_activities': 0,
                'completion_rate': 0,
                'average_mood_improvement': 0,
                'most_effective_categories': [],
                'common_barriers': [],
                'recommendations': []
            }
        
        # Calculate metrics
        completed_activities = [a for a in activities if a.is_completed]
        completion_rate = len(completed_activities) / len(activities) * 100
        
        # Mood improvements
        mood_improvements = [a.mood_change for a in completed_activities if a.mood_change is not None]
        avg_mood_improvement = sum(mood_improvements) / len(mood_improvements) if mood_improvements else 0
        
        # Most effective categories
        category_effectiveness = {}
        for activity in completed_activities:
            if activity.activity_category not in category_effectiveness:
                category_effectiveness[activity.activity_category] = []
            effectiveness = activity.get_activity_effectiveness()
            if effectiveness is not None:
                category_effectiveness[activity.activity_category].append(effectiveness)
        
        most_effective = []
        for category, scores in category_effectiveness.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                most_effective.append({'category': category, 'average_effectiveness': avg_score})
        
        most_effective.sort(key=lambda x: x['average_effectiveness'], reverse=True)
        
        # Common barriers
        all_barriers = []
        for activity in completed_activities:
            if activity.barriers_encountered:
                all_barriers.extend(activity.barriers_encountered)
        
        barrier_counts = {}
        for barrier in all_barriers:
            barrier_counts[barrier] = barrier_counts.get(barrier, 0) + 1
        
        common_barriers = sorted(barrier_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Generate recommendations
        recommendations = []
        
        if completion_rate < 50:
            recommendations.append("Try scheduling fewer activities to increase completion rate")
        
        if avg_mood_improvement < 1:
            recommendations.append("Focus on activities that have shown mood improvement")
        
        if most_effective:
            best_category = most_effective[0]['category']
            recommendations.append(f"Schedule more {best_category} activities - they're most effective for you")
        
        if common_barriers:
            top_barrier = common_barriers[0][0]
            recommendations.append(f"Address the barrier: {top_barrier}")
        
        return {
            'total_activities': len(activities),
            'completion_rate': round(completion_rate, 1),
            'average_mood_improvement': round(avg_mood_improvement, 1),
            'most_effective_categories': most_effective[:3],
            'common_barriers': [{'barrier': b, 'count': c} for b, c in common_barriers],
            'recommendations': recommendations
        }
    
    @classmethod
    def suggest_activities(cls, user_id, category=None, mood_level=None):
        """Suggest activities based on user preferences and current state"""
        # Base activity suggestions
        activity_suggestions = {
            'pleasurable': [
                'Listen to your favorite music',
                'Watch a funny movie or show',
                'Take a warm bath or shower',
                'Read a book you enjoy',
                'Spend time in nature',
                'Cook or bake something you like',
                'Call a friend or family member',
                'Do a hobby you enjoy',
                'Take photos of things you find beautiful',
                'Listen to a podcast you like'
            ],
            'mastery': [
                'Complete a small task you\'ve been putting off',
                'Learn something new for 15 minutes',
                'Organize a small area of your space',
                'Practice a skill you want to improve',
                'Write in a journal',
                'Plan your day or week',
                'Complete a puzzle or brain game',
                'Try a new recipe',
                'Work on a project you care about',
                'Set a small goal and work toward it'
            ],
            'social': [
                'Text or call a friend',
                'Spend time with family',
                'Join an online community',
                'Volunteer for a cause you care about',
                'Attend a virtual event',
                'Share something positive on social media',
                'Write a thank you note to someone',
                'Join a study group or club',
                'Have a video call with someone',
                'Participate in a group activity'
            ],
            'physical': [
                'Take a 10-minute walk',
                'Do some gentle stretching',
                'Dance to your favorite song',
                'Do some light exercise',
                'Go for a bike ride',
                'Do yoga or meditation',
                'Play a sport you enjoy',
                'Go swimming if possible',
                'Do some gardening',
                'Take the stairs instead of elevator'
            ]
        }
        
        # Filter based on category
        if category and category in activity_suggestions:
            suggestions = activity_suggestions[category]
        else:
            suggestions = []
            for cat_suggestions in activity_suggestions.values():
                suggestions.extend(cat_suggestions)
        
        # Adjust based on mood level
        if mood_level and mood_level <= 3:  # Low mood
            # Suggest easier, more accessible activities
            suggestions = [s for s in suggestions if any(word in s.lower() for word in 
                ['small', 'gentle', 'easy', 'simple', 'short', 'light'])]
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def __repr__(self):
        return f'<BehavioralActivation {self.id}: {self.activity_name} - {self.activity_category}>'
