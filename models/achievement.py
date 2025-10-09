"""
Achievement Model for WellnessWeavers
Gamification system with comprehensive tracking and rewards
"""

from database import db
from datetime import datetime
import json

class Achievement(db.Model):
    """Enhanced Achievement model for gamification and motivation"""
    __tablename__ = 'achievements'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL for templates
    
    # Achievement details
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # FontAwesome icon name or emoji
    badge_color = db.Column(db.String(20), default='#38b2ac')  # Hex color code
    
    # Gamification elements
    points = db.Column(db.Integer, default=0)
    rarity = db.Column(db.String(20), default='common')  # common, uncommon, rare, epic, legendary
    category = db.Column(db.String(50))  # mood, conversation, streak, milestone, etc.
    
    # Achievement criteria and progress
    achievement_type = db.Column(db.String(50), nullable=False)  # count, streak, milestone, special
    target_value = db.Column(db.Integer)  # Target number for completion
    current_progress = db.Column(db.Integer, default=0)  # Current progress
    progress_unit = db.Column(db.String(20))  # days, entries, conversations, etc.
    
    # Conditions for earning
    criteria = db.Column(db.JSON)  # Complex conditions for earning achievement
    prerequisites = db.Column(db.JSON)  # Other achievements needed first
    
    # Achievement metadata
    is_hidden = db.Column(db.Boolean, default=False)  # Hidden until unlocked
    is_repeatable = db.Column(db.Boolean, default=False)  # Can be earned multiple times
    is_template = db.Column(db.Boolean, default=False)  # Template for creating user achievements
    tier = db.Column(db.Integer, default=1)  # Achievement tier (1-5)
    
    # Cultural and seasonal elements
    cultural_context = db.Column(db.JSON)  # Specific to certain cultures/regions
    seasonal = db.Column(db.String(50))  # Special seasonal achievements
    festival_related = db.Column(db.String(100))  # Related to specific festivals
    
    # Progress tracking
    earned = db.Column(db.Boolean, default=False)
    earned_at = db.Column(db.DateTime)
    times_earned = db.Column(db.Integer, default=0)  # For repeatable achievements
    
    # Engagement features
    celebration_shown = db.Column(db.Boolean, default=False)
    shared_publicly = db.Column(db.Boolean, default=False)
    social_impact_score = db.Column(db.Float, default=0.0)  # How inspiring to others
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_progress_update = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # For time-limited achievements
    
    # Relationships
    user = db.relationship('User', back_populates='achievements')
    
    def check_progress(self, user_data):
        """Check and update achievement progress based on user data"""
        if self.earned and not self.is_repeatable:
            return False
        
        try:
            # Different progress calculation based on achievement type
            if self.achievement_type == 'mood_streak':
                new_progress = user_data.get('streak_days', 0)
            elif self.achievement_type == 'mood_count':
                new_progress = user_data.get('total_mood_entries', 0)
            elif self.achievement_type == 'conversation_count':
                new_progress = user_data.get('total_conversations', 0)
            elif self.achievement_type == 'points_milestone':
                new_progress = user_data.get('total_points', 0)
            elif self.achievement_type == 'wellness_score':
                new_progress = int(user_data.get('wellness_score', 0))
            elif self.achievement_type == 'habit_consistency':
                new_progress = user_data.get('habit_streak', 0)
            else:
                # Custom criteria evaluation
                new_progress = self._evaluate_custom_criteria(user_data)
            
            # Update progress
            if new_progress > self.current_progress:
                self.current_progress = new_progress
                self.last_progress_update = datetime.utcnow()
                
                # Check if achievement is earned
                if new_progress >= self.target_value and not self.earned:
                    return self._earn_achievement()
            
            return False
            
        except Exception as e:
            print(f"Error checking progress for achievement {self.id}: {str(e)}")
            return False
    
    def _evaluate_custom_criteria(self, user_data):
        """Evaluate complex custom criteria"""
        if not self.criteria:
            return 0
        
        try:
            # Example criteria evaluation
            # This would be expanded based on specific achievement needs
            criteria = self.criteria
            
            if criteria.get('type') == 'mood_variety':
                # Achievement for logging different emotions
                unique_emotions = len(set(user_data.get('emotions_logged', [])))
                return unique_emotions
            
            elif criteria.get('type') == 'time_based':
                # Achievement for consistency over time
                days_active = user_data.get('days_active_in_period', 0)
                required_days = criteria.get('required_days', 7)
                return days_active if days_active >= required_days else 0
            
            elif criteria.get('type') == 'improvement':
                # Achievement for improvement in wellness score
                improvement = user_data.get('wellness_improvement', 0)
                return improvement
                
            return 0
            
        except Exception as e:
            print(f"Error evaluating criteria for achievement {self.id}: {str(e)}")
            return 0
    
    def _earn_achievement(self):
        """Mark achievement as earned and handle rewards"""
        self.earned = True
        self.earned_at = datetime.utcnow()
        self.times_earned += 1
        
        # Add points to user
        if self.user:
            self.user.add_experience_points(self.points)
        
        # Create celebration notification
        self._create_celebration()
        
        return True
    
    def _create_celebration(self):
        """Create a celebration for earning this achievement"""
        # This would integrate with notification system
        celebration_data = {
            'type': 'achievement_earned',
            'achievement_id': self.id,
            'title': self.title,
            'points': self.points,
            'rarity': self.rarity,
            'celebration_style': self._get_celebration_style()
        }
        
        # Store celebration data or trigger notification
        # Implementation would depend on notification system
        return celebration_data
    
    def _get_celebration_style(self):
        """Get celebration style based on rarity and importance"""
        if self.rarity == 'legendary':
            return 'confetti_explosion'
        elif self.rarity == 'epic':
            return 'fireworks'
        elif self.rarity == 'rare':
            return 'sparkles'
        else:
            return 'simple_badge'
    
    def get_progress_percentage(self):
        """Get achievement progress as percentage"""
        if not self.target_value or self.target_value <= 0:
            return 0
        
        progress = min(100, (self.current_progress / self.target_value) * 100)
        return round(progress, 1)
    
    def get_next_milestone(self):
        """Get next milestone or completion target"""
        if self.earned and not self.is_repeatable:
            return None
        
        if self.current_progress >= self.target_value:
            if self.is_repeatable:
                return {
                    'type': 'repeat',
                    'target': self.target_value,
                    'description': f'Earn this achievement again!'
                }
            return None
        
        remaining = self.target_value - self.current_progress
        return {
            'type': 'completion',
            'target': self.target_value,
            'remaining': remaining,
            'description': f'{remaining} more {self.progress_unit} to unlock'
        }
    
    def get_sharing_content(self):
        """Get content for sharing achievement"""
        return {
            'title': f'🎉 Achievement Unlocked: {self.title}',
            'description': self.description,
            'points': self.points,
            'rarity': self.rarity,
            'category': self.category,
            'image_url': self._generate_badge_image_url(),
            'share_text': f'I just earned the "{self.title}" achievement in WellnessWeavers! 🎉 #{self.category} #MentalHealthJourney'
        }
    
    def _generate_badge_image_url(self):
        """Generate URL for achievement badge image"""
        # This would generate or return URL to achievement badge
        return f'/static/images/badges/{self.category}_{self.rarity}.png'
    
    def to_dict(self, include_progress=True):
        """Convert achievement to dictionary"""
        achievement_dict = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'badge_color': self.badge_color,
            'points': self.points,
            'rarity': self.rarity,
            'category': self.category,
            'tier': self.tier,
            'earned': self.earned,
            'times_earned': self.times_earned,
            'is_hidden': self.is_hidden,
            'is_repeatable': self.is_repeatable
        }
        
        if include_progress and not self.is_hidden:
            achievement_dict.update({
                'current_progress': self.current_progress,
                'target_value': self.target_value,
                'progress_percentage': self.get_progress_percentage(),
                'next_milestone': self.get_next_milestone(),
                'progress_unit': self.progress_unit
            })
        
        if self.earned:
            achievement_dict.update({
                'earned_at': self.earned_at.isoformat() if self.earned_at else None,
                'sharing_content': self.get_sharing_content()
            })
        
        return achievement_dict
    
    @classmethod
    def create_default_achievements(cls):
        """Create default achievement templates for new users"""
        default_achievements = [
            # Streak Achievements
            {
                'title': 'First Steps',
                'description': 'Log your first mood entry',
                'icon': '👶',
                'category': 'milestone',
                'achievement_type': 'mood_count',
                'target_value': 1,
                'points': 25,
                'rarity': 'common'
            },
            {
                'title': 'Week Warrior',
                'description': 'Maintain a 7-day mood tracking streak',
                'icon': '🔥',
                'category': 'streak',
                'achievement_type': 'mood_streak',
                'target_value': 7,
                'points': 100,
                'rarity': 'uncommon'
            },
            {
                'title': 'Consistency Champion',
                'description': 'Maintain a 30-day mood tracking streak',
                'icon': '💪',
                'category': 'streak',
                'achievement_type': 'mood_streak',
                'target_value': 30,
                'points': 500,
                'rarity': 'rare'
            },
            
            # Conversation Achievements
            {
                'title': 'Chatty Cathy',
                'description': 'Have 10 conversations with your AI companion',
                'icon': '💬',
                'category': 'conversation',
                'achievement_type': 'conversation_count',
                'target_value': 10,
                'points': 75,
                'rarity': 'common'
            },
            {
                'title': 'Deep Thinker',
                'description': 'Have 50 meaningful conversations',
                'icon': '🧠',
                'category': 'conversation',
                'achievement_type': 'conversation_count',
                'target_value': 50,
                'points': 300,
                'rarity': 'uncommon'
            },
            
            # Wellness Achievements
            {
                'title': 'Wellness Warrior',
                'description': 'Achieve a wellness score of 80 or higher',
                'icon': '⭐',
                'category': 'wellness',
                'achievement_type': 'wellness_score',
                'target_value': 80,
                'points': 200,
                'rarity': 'uncommon'
            },
            {
                'title': 'Emotional Intelligence',
                'description': 'Log 10 different emotions',
                'icon': '🎭',
                'category': 'mood',
                'achievement_type': 'custom',
                'target_value': 10,
                'points': 150,
                'rarity': 'uncommon',
                'criteria': {'type': 'mood_variety'}
            },
            
            # Points Milestones
            {
                'title': 'Point Collector',
                'description': 'Earn your first 1000 points',
                'icon': '💎',
                'category': 'milestone',
                'achievement_type': 'points_milestone',
                'target_value': 1000,
                'points': 100,
                'rarity': 'common'
            },
            {
                'title': 'Points Master',
                'description': 'Earn 5000 points',
                'icon': '👑',
                'category': 'milestone',
                'achievement_type': 'points_milestone',
                'target_value': 5000,
                'points': 500,
                'rarity': 'rare'
            },
            
            # Special Cultural Achievements
            {
                'title': 'Festival Joy',
                'description': 'Log positive mood during Diwali season',
                'icon': '🪔',
                'category': 'cultural',
                'achievement_type': 'custom',
                'target_value': 1,
                'points': 50,
                'rarity': 'uncommon',
                'seasonal': 'diwali',
                'cultural_context': ['hindu', 'indian']
            }
        ]
        
        achievement_templates = []
        for ach_data in default_achievements:
            achievement = cls(
                is_template=True,
                **ach_data
            )
            achievement_templates.append(achievement)
        
        return achievement_templates
    
    @classmethod
    def create_user_achievements_from_templates(cls, user_id):
        """Create user-specific achievements from templates"""
        templates = cls.query.filter_by(is_template=True).all()
        user_achievements = []
        
        for template in templates:
            # Check cultural relevance
            if template.cultural_context:
                # Would check user's cultural background
                # For now, create all achievements
                pass
            
            user_achievement = cls(
                user_id=user_id,
                title=template.title,
                description=template.description,
                icon=template.icon,
                badge_color=template.badge_color,
                points=template.points,
                rarity=template.rarity,
                category=template.category,
                achievement_type=template.achievement_type,
                target_value=template.target_value,
                progress_unit=template.progress_unit,
                criteria=template.criteria,
                prerequisites=template.prerequisites,
                is_hidden=template.is_hidden,
                is_repeatable=template.is_repeatable,
                tier=template.tier,
                cultural_context=template.cultural_context,
                seasonal=template.seasonal,
                festival_related=template.festival_related
            )
            user_achievements.append(user_achievement)
        
        return user_achievements
    
    @classmethod
    def update_user_achievements(cls, user_id, user_data):
        """Update all achievements for a user based on their current data"""
        user_achievements = cls.query.filter_by(user_id=user_id).all()
        newly_earned = []
        
        for achievement in user_achievements:
            if achievement.check_progress(user_data):
                newly_earned.append(achievement)
        
        return newly_earned
    
    @classmethod
    def check_and_award_achievements(cls, user):
        """Check and award achievements for a user"""
        from models.mood import Mood
        from models.conversation import Conversation
        
        # Get user's current data
        user_data = {
            'mood_entries': Mood.query.filter_by(user_id=user.id).count(),
            'conversations': Conversation.query.filter_by(user_id=user.id).count(),
            'streak_days': user.streak_days,
            'wellness_score': user.wellness_score,
            'total_points': user.total_points,
            'level': user.level
        }
        
        # Get user's achievements
        user_achievements = cls.query.filter_by(user_id=user.id).all()
        newly_earned = []
        
        for achievement in user_achievements:
            if not achievement.earned and achievement.check_progress(user_data):
                newly_earned.append(achievement)
                # Award points
                user.add_experience_points(achievement.points)
        
        return newly_earned
    
    @classmethod
    def get_user_progress(cls, user):
        """Get user's achievement progress"""
        user_achievements = cls.query.filter_by(user_id=user.id).all()
        
        progress = {
            'total_achievements': len(user_achievements),
            'earned_achievements': len([a for a in user_achievements if a.earned]),
            'in_progress': len([a for a in user_achievements if not a.earned and a.current_progress > 0]),
            'not_started': len([a for a in user_achievements if not a.earned and a.current_progress == 0]),
            'achievements': []
        }
        
        for achievement in user_achievements:
            progress['achievements'].append({
                'id': achievement.id,
                'title': achievement.title,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'current_progress': achievement.current_progress,
                'target_value': achievement.target_value,
                'earned': achievement.earned,
                'progress_percentage': (achievement.current_progress / achievement.target_value * 100) if achievement.target_value > 0 else 0
            })
        
        return progress
    
    def __repr__(self):
        status = "✅" if self.earned else "⏳"
        return f'<Achievement {self.title} {status}: {self.current_progress}/{self.target_value}>'