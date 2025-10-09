"""
Habit Tracker Models for WellnessWeavers
Comprehensive habit management with tracking and insights
"""

from database import db
from datetime import datetime, date, timedelta
import json

class HabitTracker(db.Model):
    """Individual habit tracking with comprehensive analytics"""
    __tablename__ = 'habit_trackers'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Habit details
    habit_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # exercise, meditation, sleep, social, creative, etc.
    
    # Visual customization
    color = db.Column(db.String(20), default='#38b2ac')  # Hex color
    icon = db.Column(db.String(50), default='fa-check')  # FontAwesome icon
    emoji = db.Column(db.String(10))  # Emoji representation
    
    # Frequency and targets
    target_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    target_count = db.Column(db.Integer, default=1)  # How many times per frequency
    measurement_unit = db.Column(db.String(20))  # minutes, times, pages, etc.
    
    # Current progress
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    total_completions = db.Column(db.Integer, default=0)
    last_completed_date = db.Column(db.Date)
    
    # Scheduling
    scheduled_times = db.Column(db.JSON)  # Preferred times ["09:00", "18:00"]
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_advance_minutes = db.Column(db.Integer, default=15)
    
    # Motivation and gamification
    motivation_reason = db.Column(db.Text)  # Why user wants this habit
    reward_after_streak = db.Column(db.String(200))  # Self-reward after X days
    reward_streak_target = db.Column(db.Integer, default=7)
    
    # Difficulty and adaptation
    difficulty_level = db.Column(db.Integer, default=3)  # 1-5 scale
    auto_adjust_difficulty = db.Column(db.Boolean, default=True)
    
    # Tracking preferences
    requires_proof = db.Column(db.Boolean, default=False)  # Photo/note required
    track_mood_impact = db.Column(db.Boolean, default=True)
    track_energy_impact = db.Column(db.Boolean, default=True)
    
    # Status and settings
    is_active = db.Column(db.Boolean, default=True)
    is_archived = db.Column(db.Boolean, default=False)
    privacy_level = db.Column(db.String(20), default='private')  # private, friends, public
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paused_at = db.Column(db.DateTime)  # When habit was paused
    
    # Relationships
    user = db.relationship('User', back_populates='habit_trackers')
    entries = db.relationship('HabitEntry', back_populates='habit', lazy='dynamic', cascade='all, delete-orphan')
    
    def log_completion(self, completed=True, notes='', proof_data=None, mood_before=None, mood_after=None, energy_before=None, energy_after=None):
        """Log a habit completion or skip"""
        today = date.today()
        
        # Check if already logged today
        existing_entry = HabitEntry.query.filter_by(
            habit_id=self.id,
            date=today
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.completed = completed
            existing_entry.notes = notes
            existing_entry.proof_data = proof_data
            existing_entry.mood_before = mood_before
            existing_entry.mood_after = mood_after
            existing_entry.energy_before = energy_before
            existing_entry.energy_after = energy_after
            existing_entry.updated_at = datetime.utcnow()
            entry = existing_entry
        else:
            # Create new entry
            entry = HabitEntry(
                habit_id=self.id,
                date=today,
                completed=completed,
                notes=notes,
                proof_data=proof_data,
                mood_before=mood_before,
                mood_after=mood_after,
                energy_before=energy_before,
                energy_after=energy_after
            )
            db.session.add(entry)
        
        if completed:
            self._update_completion_stats()
        
        return entry
    
    def _update_completion_stats(self):
        """Update streak and completion statistics"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Update total completions
        self.total_completions += 1
        self.last_completed_date = today
        
        # Update streak
        yesterday_entry = HabitEntry.query.filter_by(
            habit_id=self.id,
            date=yesterday,
            completed=True
        ).first()
        
        if yesterday_entry or self.current_streak == 0:
            self.current_streak += 1
        else:
            self.current_streak = 1  # Start new streak
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
    
    def calculate_completion_rate(self, days=30):
        """Calculate completion rate over specified days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        entries = HabitEntry.query.filter(
            HabitEntry.habit_id == self.id,
            HabitEntry.date >= start_date,
            HabitEntry.date <= end_date
        ).all()
        
        if not entries:
            return 0.0
        
        completed_days = sum(1 for entry in entries if entry.completed)
        total_days = min(days, (end_date - self.created_at.date()).days + 1)
        
        return (completed_days / total_days) * 100 if total_days > 0 else 0.0
    
    def get_streak_status(self):
        """Get current streak status and next target"""
        today = date.today()
        
        # Check if streak is broken (no entry yesterday)
        if self.last_completed_date and self.last_completed_date < today - timedelta(days=1):
            return {
                'status': 'broken',
                'current_streak': 0,
                'days_since_break': (today - self.last_completed_date).days,
                'message': f'Streak broken {(today - self.last_completed_date).days} days ago'
            }
        
        # Check if completed today
        today_entry = HabitEntry.query.filter_by(
            habit_id=self.id,
            date=today,
            completed=True
        ).first()
        
        if today_entry:
            return {
                'status': 'active',
                'current_streak': self.current_streak,
                'next_milestone': self._get_next_milestone(),
                'message': f'Great job! {self.current_streak} day streak!'
            }
        else:
            return {
                'status': 'pending',
                'current_streak': self.current_streak,
                'message': 'Ready to continue your streak today?',
                'risk_level': 'high' if self.current_streak > 7 else 'medium'
            }
    
    def _get_next_milestone(self):
        """Get next streak milestone to aim for"""
        milestones = [7, 14, 21, 30, 50, 100, 365]
        
        for milestone in milestones:
            if self.current_streak < milestone:
                return {
                    'target': milestone,
                    'days_to_go': milestone - self.current_streak,
                    'description': f'{milestone} day milestone'
                }
        
        # If beyond all milestones
        next_hundred = ((self.current_streak // 100) + 1) * 100
        return {
            'target': next_hundred,
            'days_to_go': next_hundred - self.current_streak,
            'description': f'{next_hundred} day milestone'
        }
    
    def get_mood_energy_correlation(self, days=30):
        """Analyze correlation between habit and mood/energy"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        entries = HabitEntry.query.filter(
            HabitEntry.habit_id == self.id,
            HabitEntry.date >= start_date,
            HabitEntry.mood_before.isnot(None),
            HabitEntry.mood_after.isnot(None)
        ).all()
        
        if len(entries) < 5:  # Need minimum data
            return None
        
        mood_improvements = []
        energy_improvements = []
        
        for entry in entries:
            if entry.completed:
                mood_diff = entry.mood_after - entry.mood_before
                mood_improvements.append(mood_diff)
                
                if entry.energy_before and entry.energy_after:
                    energy_diff = entry.energy_after - entry.energy_before
                    energy_improvements.append(energy_diff)
        
        avg_mood_improvement = sum(mood_improvements) / len(mood_improvements) if mood_improvements else 0
        avg_energy_improvement = sum(energy_improvements) / len(energy_improvements) if energy_improvements else 0
        
        return {
            'mood_impact': {
                'average_improvement': round(avg_mood_improvement, 1),
                'interpretation': self._interpret_mood_impact(avg_mood_improvement)
            },
            'energy_impact': {
                'average_improvement': round(avg_energy_improvement, 1),
                'interpretation': self._interpret_energy_impact(avg_energy_improvement)
            } if energy_improvements else None,
            'sample_size': len(entries)
        }
    
    def _interpret_mood_impact(self, avg_improvement):
        """Interpret mood improvement score"""
        if avg_improvement >= 2:
            return 'Significant positive impact on mood'
        elif avg_improvement >= 1:
            return 'Moderate positive impact on mood'
        elif avg_improvement >= 0.5:
            return 'Slight positive impact on mood'
        elif avg_improvement >= -0.5:
            return 'Neutral impact on mood'
        else:
            return 'May negatively impact mood'
    
    def _interpret_energy_impact(self, avg_improvement):
        """Interpret energy improvement score"""
        if avg_improvement >= 2:
            return 'Significantly boosts energy levels'
        elif avg_improvement >= 1:
            return 'Moderately increases energy'
        elif avg_improvement >= 0.5:
            return 'Slightly increases energy'
        elif avg_improvement >= -0.5:
            return 'Neutral impact on energy'
        else:
            return 'May decrease energy levels'
    
    def get_recommendations(self):
        """Get personalized recommendations for this habit"""
        recommendations = []
        completion_rate = self.calculate_completion_rate(30)
        streak_status = self.get_streak_status()
        
        # Low completion rate recommendations
        if completion_rate < 50:
            recommendations.append({
                'type': 'improvement',
                'title': 'Boost Your Success Rate',
                'message': f'Your completion rate is {completion_rate:.1f}%. Let\'s make it easier!',
                'suggestions': [
                    'Reduce the frequency or difficulty',
                    'Set up better reminders',
                    'Link it to an existing habit'
                ]
            })
        
        # Streak maintenance
        if streak_status['status'] == 'pending' and self.current_streak > 5:
            recommendations.append({
                'type': 'urgent',
                'title': 'Don\'t Break Your Streak!',
                'message': f'You have a {self.current_streak} day streak going. Complete today to keep it alive!',
                'suggestions': ['Set a reminder for later today', 'Do a mini version if short on time']
            })
        
        # Milestone approaching
        next_milestone = self._get_next_milestone()
        if next_milestone['days_to_go'] <= 3:
            recommendations.append({
                'type': 'motivation',
                'title': 'Milestone Almost There!',
                'message': f'Only {next_milestone["days_to_go"]} days until your {next_milestone["target"]} day milestone!',
                'suggestions': ['Stay focused', 'Plan a celebration']
            })
        
        # Time-based recommendations
        if self.scheduled_times:
            recommendations.append({
                'type': 'timing',
                'title': 'Optimal Timing',
                'message': f'Your scheduled times: {", ".join(self.scheduled_times)}',
                'suggestions': ['Stick to your scheduled times for best results']
            })
        
        return recommendations
    
    def to_dict(self, include_analytics=False):
        """Convert to dictionary representation"""
        habit_dict = {
            'id': self.id,
            'habit_name': self.habit_name,
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'icon': self.icon,
            'emoji': self.emoji,
            'target_frequency': self.target_frequency,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'total_completions': self.total_completions,
            'last_completed_date': self.last_completed_date.isoformat() if self.last_completed_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_analytics:
            habit_dict.update({
                'completion_rate_30d': self.calculate_completion_rate(30),
                'streak_status': self.get_streak_status(),
                'mood_energy_correlation': self.get_mood_energy_correlation(),
                'recommendations': self.get_recommendations()
            })
        
        return habit_dict
    
    def __repr__(self):
        return f'<HabitTracker {self.habit_name}: {self.current_streak} day streak>'


class HabitEntry(db.Model):
    """Individual habit completion entries"""
    __tablename__ = 'habit_entries'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit_trackers.id'), nullable=False)
    
    # Entry details
    date = db.Column(db.Date, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=True)
    partial_completion = db.Column(db.Float)  # 0-1 for partial completions
    
    # Context and notes
    notes = db.Column(db.Text)
    location = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)  # How long it took
    
    # Mood and energy tracking
    mood_before = db.Column(db.Integer)  # 1-10 scale
    mood_after = db.Column(db.Integer)   # 1-10 scale
    energy_before = db.Column(db.Integer)  # 1-10 scale
    energy_after = db.Column(db.Integer)   # 1-10 scale
    
    # Proof and validation
    proof_data = db.Column(db.JSON)  # Photos, measurements, etc.
    verification_required = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))  # Accountability partner
    
    # Difficulty and satisfaction
    perceived_difficulty = db.Column(db.Integer)  # 1-5 how hard it was
    satisfaction_level = db.Column(db.Integer)   # 1-5 how satisfying
    
    # External factors
    weather = db.Column(db.String(50))
    companions = db.Column(db.JSON)  # Who was with you
    obstacles_faced = db.Column(db.JSON)  # What made it challenging
    
    # Timestamps
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    habit = db.relationship('HabitTracker', back_populates='entries')
    
    def calculate_impact_score(self):
        """Calculate the positive impact of this habit completion"""
        impact = 0
        
        # Base completion points
        if self.completed:
            impact += 5
        elif self.partial_completion:
            impact += self.partial_completion * 5
        
        # Mood improvement bonus
        if self.mood_before and self.mood_after:
            mood_improvement = self.mood_after - self.mood_before
            impact += mood_improvement * 0.5
        
        # Energy improvement bonus
        if self.energy_before and self.energy_after:
            energy_improvement = self.energy_after - self.energy_before
            impact += energy_improvement * 0.3
        
        # Satisfaction bonus
        if self.satisfaction_level:
            impact += (self.satisfaction_level - 3) * 0.5  # Neutral at 3
        
        # Difficulty consideration (harder habits worth more)
        if self.perceived_difficulty:
            impact += (self.perceived_difficulty - 1) * 0.2
        
        return max(0, min(10, impact))  # Clamp between 0-10
    
    def get_insights(self):
        """Generate insights from this habit entry"""
        insights = []
        
        # Mood impact insight
        if self.mood_before and self.mood_after:
            mood_change = self.mood_after - self.mood_before
            if mood_change >= 2:
                insights.append({
                    'type': 'positive',
                    'message': f'This habit improved your mood by {mood_change} points!'
                })
            elif mood_change <= -2:
                insights.append({
                    'type': 'concern',
                    'message': f'This habit may have decreased your mood by {abs(mood_change)} points.'
                })
        
        # Energy impact insight
        if self.energy_before and self.energy_after:
            energy_change = self.energy_after - self.energy_before
            if energy_change >= 2:
                insights.append({
                    'type': 'positive',
                    'message': f'Great energy boost of {energy_change} points!'
                })
        
        # Difficulty vs satisfaction
        if self.perceived_difficulty and self.satisfaction_level:
            if self.satisfaction_level >= 4 and self.perceived_difficulty >= 3:
                insights.append({
                    'type': 'achievement',
                    'message': 'You overcame a challenge and felt great about it!'
                })
        
        return insights
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'completed': self.completed,
            'partial_completion': self.partial_completion,
            'notes': self.notes,
            'duration_minutes': self.duration_minutes,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after,
            'energy_before': self.energy_before,
            'energy_after': self.energy_after,
            'perceived_difficulty': self.perceived_difficulty,
            'satisfaction_level': self.satisfaction_level,
            'impact_score': self.calculate_impact_score(),
            'insights': self.get_insights(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        status = "✅" if self.completed else "⏸️"
        return f'<HabitEntry {self.date} {status}: {self.habit.habit_name if self.habit else "Unknown"}>'