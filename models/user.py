"""
User Model for WellnessWeavers
Comprehensive user management with authentication and wellness tracking
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db
import json

class User(UserMixin, db.Model):
    """Enhanced User model with comprehensive mental health features"""
    __tablename__ = 'users'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True, index=True)  # Firebase UID
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for Firebase-only users
    
    # Profile information
    full_name = db.Column(db.String(100))
    age_range = db.Column(db.String(20))  # "18-25", "26-35", etc.
    gender = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))
    
    # Cultural and language preferences
    preferred_language = db.Column(db.String(10), default='en')
    secondary_languages = db.Column(db.JSON)  # List of language codes
    cultural_background = db.Column(db.String(100))
    location_city = db.Column(db.String(100))
    location_state = db.Column(db.String(100))
    location_country = db.Column(db.String(100), default='India')
    
    # Wellness metrics and gamification
    wellness_score = db.Column(db.Float, default=50.0)  # 0-100 scale
    total_points = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience_points = db.Column(db.Integer, default=0)
    
    # Mental health specific
    mental_health_goals = db.Column(db.JSON)  # List of goals
    therapy_preferences = db.Column(db.JSON)  # Preferred therapy types
    crisis_plan_enabled = db.Column(db.Boolean, default=False)
    
    # Account settings and subscription
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    phone_verified_at = db.Column(db.DateTime)
    subscription_tier = db.Column(db.String(20), default='free')  # free, premium, professional
    subscription_expires_at = db.Column(db.DateTime)
    
    # Privacy and notification settings
    privacy_level = db.Column(db.String(20), default='standard')  # minimal, standard, open
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    
    # AI and personalization preferences
    ai_companion_personality = db.Column(db.String(50), default='supportive_friend')
    conversation_style = db.Column(db.String(50), default='casual')
    therapy_reminder_frequency = db.Column(db.String(20), default='weekly')
    
    # Activity and engagement tracking
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.Integer, default=0)
    first_mood_entry_at = db.Column(db.DateTime)
    first_conversation_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, index=True)
    last_activity = db.Column(db.DateTime, index=True)
    last_mood_check = db.Column(db.DateTime)
    
    # Relationships (defined with back_populates for clarity)
    moods = db.relationship('Mood', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    voice_journals = db.relationship('VoiceJournal', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    habit_trackers = db.relationship('HabitTracker', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    medications = db.relationship('Medication', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    therapy_sessions = db.relationship('TherapySession', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('Goal', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    crisis_alerts = db.relationship('CrisisAlert', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    emergency_contacts = db.relationship('EmergencyContact', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    sleep_logs = db.relationship('SleepLog', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    social_interactions = db.relationship('SocialInteraction', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    safety_plans = db.relationship('SafetyPlan', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def create_from_firebase(cls, firebase_user_data):
        """Create user from Firebase authentication data"""
        user = cls(
            firebase_uid=firebase_user_data['uid'],
            email=firebase_user_data.get('email'),
            username=firebase_user_data.get('email', '').split('@')[0],  # Default username from email
            full_name=firebase_user_data.get('name'),
            is_verified=firebase_user_data.get('email_verified', False),
            email_verified_at=datetime.utcnow() if firebase_user_data.get('email_verified') else None
        )
        return user
    
    @classmethod
    def get_by_firebase_uid(cls, firebase_uid):
        """Get user by Firebase UID"""
        return cls.query.filter_by(firebase_uid=firebase_uid).first()
    
    def is_firebase_user(self):
        """Check if user is authenticated via Firebase"""
        return self.firebase_uid is not None
    
    def update_wellness_score(self):
        """Calculate and update wellness score based on recent activities"""
        from datetime import timedelta
        from sqlalchemy import func
        
        # Get recent mood data (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_moods = self.moods.filter(
            self.moods.c.timestamp >= week_ago
        ).all()
        
        if not recent_moods:
            return self.wellness_score
        
        # Calculate average mood score
        avg_mood = sum(mood.mood_score for mood in recent_moods) / len(recent_moods)
        
        # Factor in activity consistency
        activity_bonus = min(10, len(recent_moods))  # Consistency bonus
        
        # Factor in achievements
        achievement_bonus = min(15, self.achievements.count() * 2)
        
        # Calculate final score (weighted average)
        new_score = (avg_mood * 10) + activity_bonus + achievement_bonus
        new_score = max(0, min(100, new_score))  # Clamp between 0-100
        
        self.wellness_score = new_score
        return new_score
    
    def update_streak(self):
        """Update daily streak based on mood entries"""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Check if user logged mood today
        today_entry = self.moods.filter(
            db.func.date(self.moods.c.timestamp) == today
        ).first()
        
        if today_entry:
            # Check if they also logged yesterday
            yesterday_entry = self.moods.filter(
                db.func.date(self.moods.c.timestamp) == yesterday
            ).first()
            
            if yesterday_entry:
                self.streak_days += 1
            else:
                self.streak_days = 1  # Start new streak
            
            # Update longest streak
            if self.streak_days > self.longest_streak:
                self.longest_streak = self.streak_days
        else:
            # Check if streak should be broken
            if self.last_mood_check and self.last_mood_check.date() < yesterday:
                self.streak_days = 0
    
    def add_experience_points(self, points):
        """Add experience points and handle level progression"""
        self.experience_points += points
        self.total_points += points
        
        # Simple level progression (every 1000 XP = 1 level)
        new_level = (self.experience_points // 1000) + 1
        
        if new_level > self.level:
            self.level = new_level
            return {'level_up': True, 'new_level': new_level}
        
        return {'level_up': False, 'total_points': self.total_points}
    
    def get_wellness_insights(self):
        """Generate personalized wellness insights"""
        from datetime import timedelta
        
        insights = []
        
        # Mood trend analysis
        if self.wellness_score < 40:
            insights.append({
                'type': 'concern',
                'title': 'Wellness Score Needs Attention',
                'message': 'Your wellness score has been low. Consider reaching out to a professional.',
                'action': 'Book a therapy session',
                'priority': 'high'
            })
        elif self.wellness_score > 80:
            insights.append({
                'type': 'positive',
                'title': 'Great Mental Health Progress!',
                'message': 'Your wellness score is excellent. Keep up the good work!',
                'action': 'Share your success',
                'priority': 'low'
            })
        
        # Streak insights
        if self.streak_days >= 7:
            insights.append({
                'type': 'achievement',
                'title': f'{self.streak_days} Day Streak!',
                'message': 'Consistency is key to mental wellness.',
                'priority': 'medium'
            })
        elif self.streak_days == 0 and self.last_mood_check:
            insights.append({
                'type': 'reminder',
                'title': 'Mood Check Reminder',
                'message': 'Regular check-ins help track your progress.',
                'action': 'Log today\'s mood',
                'priority': 'medium'
            })
        
        return insights
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data for the user"""
        from datetime import timedelta
        
        # Recent mood trend
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_moods = self.moods.filter(
            self.moods.c.timestamp >= week_ago
        ).order_by(self.moods.c.timestamp.asc()).all()
        
        # Recent achievements
        recent_achievements = self.achievements.order_by(
            self.achievements.c.earned_at.desc()
        ).limit(5).all()
        
        # Active goals
        active_goals = self.goals.filter(
            self.goals.c.status == 'active'
        ).all()
        
        return {
            'wellness_score': self.wellness_score,
            'total_points': self.total_points,
            'streak_days': self.streak_days,
            'level': self.level,
            'recent_moods': [mood.to_dict() for mood in recent_moods],
            'recent_achievements': [achievement.to_dict() for achievement in recent_achievements],
            'active_goals': [goal.to_dict() for goal in active_goals],
            'insights': self.get_wellness_insights()
        }
    
    def can_access_premium_features(self):
        """Check if user has access to premium features"""
        if self.subscription_tier in ['premium', 'professional']:
            if self.subscription_expires_at:
                return datetime.utcnow() < self.subscription_expires_at
            return True
        return False
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation"""
        user_dict = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'age_range': self.age_range,
            'gender': self.gender,
            'preferred_language': self.preferred_language,
            'cultural_background': self.cultural_background,
            'location_city': self.location_city,
            'wellness_score': self.wellness_score,
            'total_points': self.total_points,
            'streak_days': self.streak_days,
            'level': self.level,
            'subscription_tier': self.subscription_tier,
            'onboarding_completed': self.onboarding_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            user_dict.update({
                'email': self.email,
                'phone_number': self.phone_number,
                'privacy_level': self.privacy_level,
                'notifications_enabled': self.notifications_enabled,
                'ai_companion_personality': self.ai_companion_personality
            })
        
        return user_dict
    
    def __repr__(self):
        return f'<User {self.username}>'