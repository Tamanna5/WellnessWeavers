"""
Safe Features Models for WellnessWeavers
Clinical-safe features with proper oversight and boundaries
"""

from database import db
from datetime import datetime, date, timedelta
import json

class SleepLog(db.Model):
    """Safe sleep tracking with mood correlation"""
    __tablename__ = 'sleep_logs'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Sleep timing
    date = db.Column(db.Date, nullable=False, index=True)
    bedtime = db.Column(db.DateTime)
    wake_time = db.Column(db.DateTime)
    hours_slept = db.Column(db.Float)
    
    # Sleep quality (subjective)
    quality_rating = db.Column(db.Integer)  # 1-5 scale
    dream_recall = db.Column(db.Boolean)
    nightmares = db.Column(db.Boolean)
    sleep_interruptions = db.Column(db.Integer, default=0)
    
    # Sleep environment
    sleep_environment = db.Column(db.String(50))  # own_room, shared, hotel, etc.
    room_temperature = db.Column(db.String(20))  # hot, cold, comfortable
    noise_level = db.Column(db.String(20))  # quiet, moderate, loud
    
    # Factors affecting sleep
    caffeine_after_2pm = db.Column(db.Boolean)
    exercise_before_bed = db.Column(db.Boolean)
    screen_time_before_bed = db.Column(db.Integer)  # minutes
    stress_level_at_bedtime = db.Column(db.Integer)  # 1-10
    
    # Sleep aids (non-prescription tracking)
    used_sleep_aid = db.Column(db.Boolean, default=False)
    sleep_aid_type = db.Column(db.String(100))  # herbal_tea, meditation, music
    
    # Next day impact
    next_day_mood = db.Column(db.Integer)  # 1-10, linked from mood tracker
    next_day_energy = db.Column(db.Integer)  # 1-10
    next_day_focus = db.Column(db.Integer)  # 1-10
    
    # Notes
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='sleep_logs')
    
    def calculate_sleep_score(self):
        """Calculate comprehensive sleep score (0-100)"""
        score = 0
        
        # Hours slept component (40 points max)
        if self.hours_slept:
            if 7 <= self.hours_slept <= 9:
                score += 40
            elif 6 <= self.hours_slept < 7 or 9 < self.hours_slept <= 10:
                score += 30
            elif 5 <= self.hours_slept < 6 or 10 < self.hours_slept <= 11:
                score += 20
            else:
                score += 10
        
        # Quality rating component (30 points max)
        if self.quality_rating:
            score += self.quality_rating * 6
        
        # Sleep interruptions penalty
        if self.sleep_interruptions:
            penalty = min(15, self.sleep_interruptions * 3)
            score -= penalty
        
        # Consistency bonus (if bedtime/wake time are regular)
        # This would require historical data comparison
        
        # Environment bonus (10 points max)
        environment_score = 0
        if self.room_temperature == 'comfortable':
            environment_score += 3
        if self.noise_level == 'quiet':
            environment_score += 3
        if not self.caffeine_after_2pm:
            environment_score += 2
        if not self.exercise_before_bed:
            environment_score += 1
        if not self.screen_time_before_bed or self.screen_time_before_bed < 30:
            environment_score += 1
        
        score += environment_score
        
        return max(0, min(100, score))
    
    def get_sleep_insights(self):
        """Generate personalized sleep insights"""
        insights = []
        
        # Sleep duration insights
        if self.hours_slept:
            if self.hours_slept < 6:
                insights.append({
                    'type': 'concern',
                    'category': 'duration',
                    'title': 'Sleep Deficit',
                    'message': f'You only slept {self.hours_slept} hours. Most adults need 7-9 hours.',
                    'recommendation': 'Try going to bed 30 minutes earlier tonight.'
                })
            elif self.hours_slept > 10:
                insights.append({
                    'type': 'info',
                    'category': 'duration',
                    'title': 'Long Sleep',
                    'message': f'You slept {self.hours_slept} hours. This might indicate sleep debt recovery.',
                    'recommendation': 'Monitor if this becomes a pattern.'
                })
            else:
                insights.append({
                    'type': 'positive',
                    'category': 'duration',
                    'title': 'Good Sleep Duration',
                    'message': f'Great! {self.hours_slept} hours is in the healthy range.',
                    'recommendation': 'Keep maintaining this sleep schedule.'
                })
        
        # Quality insights
        if self.quality_rating and self.quality_rating <= 2:
            insights.append({
                'type': 'concern',
                'category': 'quality',
                'title': 'Poor Sleep Quality',
                'message': 'You rated your sleep quality as poor.',
                'recommendation': 'Consider factors like room temperature, noise, and stress levels.'
            })
        
        # Interruption insights
        if self.sleep_interruptions and self.sleep_interruptions >= 3:
            insights.append({
                'type': 'concern',
                'category': 'interruptions',
                'title': 'Frequent Sleep Interruptions',
                'message': f'You woke up {self.sleep_interruptions} times during the night.',
                'recommendation': 'Consider what might be causing these interruptions.'
            })
        
        # Environmental insights
        if self.caffeine_after_2pm:
            insights.append({
                'type': 'tip',
                'category': 'environment',
                'title': 'Caffeine Impact',
                'message': 'You had caffeine after 2 PM, which can affect sleep quality.',
                'recommendation': 'Try avoiding caffeine 6-8 hours before bedtime.'
            })
        
        if self.screen_time_before_bed and self.screen_time_before_bed > 60:
            insights.append({
                'type': 'tip',
                'category': 'environment',
                'title': 'Screen Time Before Bed',
                'message': f'{self.screen_time_before_bed} minutes of screen time before bed can disrupt sleep.',
                'recommendation': 'Try reducing screen time to under 30 minutes before bed.'
            })
        
        return insights
    
    def to_dict(self, include_analysis=False):
        """Convert to dictionary representation"""
        sleep_dict = {
            'id': self.id,
            'date': self.date.isoformat(),
            'bedtime': self.bedtime.isoformat() if self.bedtime else None,
            'wake_time': self.wake_time.isoformat() if self.wake_time else None,
            'hours_slept': self.hours_slept,
            'quality_rating': self.quality_rating,
            'sleep_interruptions': self.sleep_interruptions,
            'notes': self.notes
        }
        
        if include_analysis:
            sleep_dict.update({
                'sleep_score': self.calculate_sleep_score(),
                'insights': self.get_sleep_insights(),
                'next_day_impact': {
                    'mood': self.next_day_mood,
                    'energy': self.next_day_energy,
                    'focus': self.next_day_focus
                }
            })
        
        return sleep_dict
    
    def __repr__(self):
        hours = f"{self.hours_slept}h" if self.hours_slept else "Unknown"
        quality = f"Q{self.quality_rating}" if self.quality_rating else "NR"
        return f'<SleepLog {self.date}: {hours} {quality}>'


class ActivityLog(db.Model):
    """Physical activity tracking focused on mental health benefits"""
    __tablename__ = 'activity_logs'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Activity details
    date = db.Column(db.Date, nullable=False, index=True)
    activity_type = db.Column(db.String(50))  # walking, yoga, dancing, sports, etc.
    duration_minutes = db.Column(db.Integer)
    intensity = db.Column(db.String(20))  # light, moderate, vigorous
    
    # Mental health focus (NOT physical metrics like weight/calories)
    mood_before = db.Column(db.Integer)  # 1-10
    mood_after = db.Column(db.Integer)   # 1-10
    energy_before = db.Column(db.Integer)  # 1-10
    energy_after = db.Column(db.Integer)   # 1-10
    stress_before = db.Column(db.Integer)  # 1-10
    stress_after = db.Column(db.Integer)   # 1-10
    
    # Enjoyment and motivation
    enjoyment_level = db.Column(db.Integer)  # 1-10
    motivation_level = db.Column(db.Integer)  # 1-10
    felt_accomplished = db.Column(db.Boolean)
    
    # Social aspects
    activity_partner = db.Column(db.String(100))  # alone, friend, family, group
    social_enjoyment = db.Column(db.Integer)  # 1-10 if with others
    
    # Environment and context
    location = db.Column(db.String(100))  # gym, home, outdoors, etc.
    weather = db.Column(db.String(50))  # if outdoors
    time_of_day = db.Column(db.String(20))  # morning, afternoon, evening
    
    # Notes and reflection
    notes = db.Column(db.Text)
    challenges_faced = db.Column(db.JSON)  # What made it difficult
    what_helped = db.Column(db.JSON)  # What made it easier/more enjoyable
    
    # Timestamps
    activity_datetime = db.Column(db.DateTime)  # When activity actually happened
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='activity_logs')
    
    def calculate_wellness_impact(self):
        """Calculate mental wellness impact of this activity"""
        impact = 0
        
        # Base points for being active
        impact += 3
        
        # Duration bonus (mental health, not calorie burn)
        if self.duration_minutes:
            if self.duration_minutes >= 30:
                impact += 5
            elif self.duration_minutes >= 15:
                impact += 3
            else:
                impact += 1
        
        # Mood improvement
        if self.mood_before and self.mood_after:
            mood_improvement = self.mood_after - self.mood_before
            impact += mood_improvement * 0.5
        
        # Energy improvement
        if self.energy_before and self.energy_after:
            energy_improvement = self.energy_after - self.energy_before
            impact += energy_improvement * 0.3
        
        # Stress reduction
        if self.stress_before and self.stress_after:
            stress_reduction = self.stress_before - self.stress_after
            impact += stress_reduction * 0.4
        
        # Enjoyment bonus
        if self.enjoyment_level and self.enjoyment_level >= 7:
            impact += 2
        
        # Social connection bonus
        if self.activity_partner and self.activity_partner != 'alone':
            impact += 1
            if self.social_enjoyment and self.social_enjoyment >= 7:
                impact += 1
        
        # Accomplishment feeling
        if self.felt_accomplished:
            impact += 2
        
        return max(0, min(15, impact))  # Cap at 15
    
    def get_activity_insights(self):
        """Generate insights from this activity"""
        insights = []
        
        # Mood impact
        if self.mood_before and self.mood_after:
            mood_change = self.mood_after - self.mood_before
            if mood_change >= 2:
                insights.append({
                    'type': 'positive',
                    'message': f'{self.activity_type.title()} improved your mood by {mood_change} points!',
                    'category': 'mood_boost'
                })
            elif mood_change <= -1:
                insights.append({
                    'type': 'info',
                    'message': f'Mood dipped after {self.activity_type}. This might indicate overexertion or other factors.',
                    'category': 'mood_check'
                })
        
        # Energy insights
        if self.energy_before and self.energy_after:
            energy_change = self.energy_after - self.energy_before
            if energy_change >= 2:
                insights.append({
                    'type': 'positive',
                    'message': f'Great energy boost from {self.activity_type}!',
                    'category': 'energy_boost'
                })
            elif energy_change <= -2:
                insights.append({
                    'type': 'info',
                    'message': 'Activity was tiring. Consider adjusting intensity or duration.',
                    'category': 'energy_management'
                })
        
        # Stress relief
        if self.stress_before and self.stress_after:
            stress_change = self.stress_before - self.stress_after
            if stress_change >= 2:
                insights.append({
                    'type': 'positive',
                    'message': f'{self.activity_type.title()} was great for stress relief!',
                    'category': 'stress_relief'
                })
        
        # Social connection
        if self.activity_partner and self.activity_partner != 'alone' and self.social_enjoyment and self.social_enjoyment >= 8:
            insights.append({
                'type': 'positive',
                'message': 'You really enjoyed the social aspect of this activity!',
                'category': 'social_connection'
            })
        
        # Consistency patterns (would require historical data)
        # This would analyze trends over time
        
        return insights
    
    def to_dict(self, include_analysis=False):
        """Convert to dictionary representation"""
        activity_dict = {
            'id': self.id,
            'date': self.date.isoformat(),
            'activity_type': self.activity_type,
            'duration_minutes': self.duration_minutes,
            'intensity': self.intensity,
            'enjoyment_level': self.enjoyment_level,
            'activity_partner': self.activity_partner,
            'location': self.location,
            'notes': self.notes
        }
        
        if include_analysis:
            activity_dict.update({
                'wellness_impact': self.calculate_wellness_impact(),
                'mood_change': (self.mood_after - self.mood_before) if self.mood_before and self.mood_after else None,
                'energy_change': (self.energy_after - self.energy_before) if self.energy_before and self.energy_after else None,
                'stress_change': (self.stress_before - self.stress_after) if self.stress_before and self.stress_after else None,
                'insights': self.get_activity_insights()
            })
        
        return activity_dict
    
    def __repr__(self):
        duration = f"{self.duration_minutes}min" if self.duration_minutes else "Unknown"
        return f'<ActivityLog {self.date}: {self.activity_type} {duration}>'


class SafetyPlan(db.Model):
    """Evidence-based safety planning for crisis situations"""
    __tablename__ = 'safety_plans'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Step 1: Warning Signs
    warning_signs = db.Column(db.JSON)  # Personal warning signs of crisis
    
    # Step 2: Internal Coping Strategies
    coping_strategies = db.Column(db.JSON)  # Things user can do alone
    
    # Step 3: Social Settings and People for Distraction
    social_distractions = db.Column(db.JSON)  # Places to go, people to be with
    
    # Step 4: People to Ask for Help
    support_contacts = db.Column(db.JSON)  # Name, phone, relationship
    
    # Step 5: Professionals to Contact
    professional_contacts = db.Column(db.JSON)  # Therapist, doctor, crisis line
    
    # Step 6: Making Environment Safe
    means_restriction = db.Column(db.JSON)  # How to reduce access to means
    
    # Step 7: Reasons for Living
    reasons_for_living = db.Column(db.JSON)  # Hope box items, reasons to stay alive
    
    # Usage and effectiveness tracking
    times_accessed = db.Column(db.Integer, default=0)
    times_accessed_in_crisis = db.Column(db.Integer, default=0)
    effectiveness_ratings = db.Column(db.JSON)  # User feedback on effectiveness
    
    # Plan metadata
    created_with_professional = db.Column(db.Boolean, default=False)
    professional_name = db.Column(db.String(200))
    last_reviewed_with_professional = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='safety_plans')
    
    def access_in_crisis(self):
        """Record that safety plan was accessed during crisis"""
        self.times_accessed_in_crisis += 1
        self.times_accessed += 1
        
        # Create crisis alert to track usage
        from models.crisis import CrisisAlert
        alert = CrisisAlert(
            user_id=self.user_id,
            severity='medium',
            trigger_source='safety_plan_access',
            context='User accessed safety plan during crisis'
        )
        db.session.add(alert)
        
        return self.get_crisis_version()
    
    def get_crisis_version(self):
        """Get simplified version optimized for crisis situations"""
        return {
            'coping_strategies': self.coping_strategies,
            'support_contacts': self.support_contacts[:3] if self.support_contacts else [],
            'professional_contacts': self.professional_contacts,
            'reasons_for_living': self.reasons_for_living[:5] if self.reasons_for_living else [],
            'crisis_hotlines': [
                {'name': 'Vandrevala Foundation', 'phone': '1860 266 2345'},
                {'name': 'iCall', 'phone': '022-25563291'},
                {'name': 'AASRA', 'phone': '022-27546669'}
            ]
        }
    
    def is_complete(self):
        """Check if safety plan has all essential components"""
        required_components = [
            self.warning_signs,
            self.coping_strategies,
            self.support_contacts,
            self.professional_contacts,
            self.reasons_for_living
        ]
        
        return all(component and len(component) > 0 for component in required_components)
    
    def get_completion_percentage(self):
        """Get completion percentage of safety plan"""
        components = [
            self.warning_signs,
            self.coping_strategies,
            self.social_distractions,
            self.support_contacts,
            self.professional_contacts,
            self.means_restriction,
            self.reasons_for_living
        ]
        
        completed = sum(1 for component in components if component and len(component) > 0)
        return (completed / len(components)) * 100
    
    def add_effectiveness_rating(self, rating, notes=''):
        """Add user feedback on safety plan effectiveness"""
        if not self.effectiveness_ratings:
            self.effectiveness_ratings = []
        
        self.effectiveness_ratings.append({
            'rating': rating,  # 1-5 scale
            'notes': notes,
            'date': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 ratings
        if len(self.effectiveness_ratings) > 10:
            self.effectiveness_ratings = self.effectiveness_ratings[-10:]
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'warning_signs': self.warning_signs,
            'coping_strategies': self.coping_strategies,
            'social_distractions': self.social_distractions,
            'support_contacts': self.support_contacts,
            'professional_contacts': self.professional_contacts,
            'means_restriction': self.means_restriction,
            'reasons_for_living': self.reasons_for_living,
            'completion_percentage': self.get_completion_percentage(),
            'is_complete': self.is_complete(),
            'times_accessed': self.times_accessed,
            'times_accessed_in_crisis': self.times_accessed_in_crisis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None
        }
    
    def __repr__(self):
        complete = "✅" if self.is_complete() else "⚠️"
        return f'<SafetyPlan {self.id} {complete}: {self.get_completion_percentage():.0f}% complete>'


class SocialInteraction(db.Model):
    """Social connection tracking for loneliness intervention"""
    __tablename__ = 'social_interactions'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Interaction details
    date = db.Column(db.Date, nullable=False, index=True)
    interaction_type = db.Column(db.String(50))  # in_person, video, phone, text, social_media
    duration_minutes = db.Column(db.Integer)
    
    # People involved
    people_count = db.Column(db.Integer, default=1)
    relationship_types = db.Column(db.JSON)  # family, friends, colleagues, strangers
    
    # Quality and emotional impact
    quality_rating = db.Column(db.Integer)  # 1-10 how meaningful the interaction was
    initiation = db.Column(db.String(20))  # self_initiated, other_initiated, mutual
    
    # Emotional outcomes
    felt_connected = db.Column(db.Boolean)
    felt_understood = db.Column(db.Boolean)
    felt_lonely = db.Column(db.Boolean)
    felt_drained = db.Column(db.Boolean)
    felt_energized = db.Column(db.Boolean)
    
    # Context
    activity = db.Column(db.String(100))  # what you did together
    location = db.Column(db.String(100))  # where interaction took place
    planned_or_spontaneous = db.Column(db.String(20))
    
    # Notes and reflection
    notes = db.Column(db.Text)
    what_went_well = db.Column(db.JSON)
    what_was_challenging = db.Column(db.JSON)
    
    # Timestamps
    interaction_datetime = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='social_interactions')
    
    def calculate_connection_score(self):
        """Calculate how fulfilling this social interaction was"""
        score = 0
        
        # Base interaction value
        score += 2
        
        # Quality rating
        if self.quality_rating:
            score += self.quality_rating * 0.5
        
        # Duration consideration
        if self.duration_minutes:
            if self.duration_minutes >= 60:
                score += 3
            elif self.duration_minutes >= 30:
                score += 2
            elif self.duration_minutes >= 15:
                score += 1
        
        # Emotional outcomes
        if self.felt_connected:
            score += 3
        if self.felt_understood:
            score += 3
        if self.felt_energized:
            score += 2
        
        # Negative factors
        if self.felt_lonely:
            score -= 2
        if self.felt_drained:
            score -= 1
        
        # Interaction type bonuses
        type_bonuses = {
            'in_person': 2,
            'video': 1,
            'phone': 1,
            'text': 0,
            'social_media': 0
        }
        score += type_bonuses.get(self.interaction_type, 0)
        
        # People count (but diminishing returns)
        if self.people_count:
            if self.people_count == 1:
                score += 1  # One-on-one bonus
            elif 2 <= self.people_count <= 4:
                score += 2  # Small group bonus
            # Large groups don't get bonus (can be overwhelming)
        
        return max(0, min(15, score))  # Cap at 15
    
    def get_loneliness_indicators(self):
        """Identify potential loneliness indicators"""
        indicators = []
        
        if self.felt_lonely:
            indicators.append({
                'type': 'direct',
                'message': 'Felt lonely despite social interaction',
                'severity': 'high'
            })
        
        if self.quality_rating and self.quality_rating <= 3:
            indicators.append({
                'type': 'quality',
                'message': 'Low-quality social interaction',
                'severity': 'medium'
            })
        
        if not self.felt_connected and not self.felt_understood:
            indicators.append({
                'type': 'disconnection',
                'message': 'Didn\'t feel connected or understood',
                'severity': 'medium'
            })
        
        if self.interaction_type == 'text' and self.duration_minutes and self.duration_minutes < 10:
            indicators.append({
                'type': 'superficial',
                'message': 'Very brief text interaction',
                'severity': 'low'
            })
        
        return indicators
    
    def to_dict(self, include_analysis=False):
        """Convert to dictionary representation"""
        interaction_dict = {
            'id': self.id,
            'date': self.date.isoformat(),
            'interaction_type': self.interaction_type,
            'duration_minutes': self.duration_minutes,
            'people_count': self.people_count,
            'quality_rating': self.quality_rating,
            'felt_connected': self.felt_connected,
            'felt_lonely': self.felt_lonely,
            'activity': self.activity,
            'notes': self.notes
        }
        
        if include_analysis:
            interaction_dict.update({
                'connection_score': self.calculate_connection_score(),
                'loneliness_indicators': self.get_loneliness_indicators()
            })
        
        return interaction_dict
    
    def __repr__(self):
        quality = f"Q{self.quality_rating}" if self.quality_rating else "NR"
        return f'<SocialInteraction {self.date}: {self.interaction_type} {quality}>'