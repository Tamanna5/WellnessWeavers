"""
Community and Support Group Models
"""

from app import db
from datetime import datetime

class SupportGroup(db.Model):
    """Community support groups"""
    __tablename__ = 'support_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    topic = db.Column(db.String(100))  # anxiety, depression, students, etc.
    
    is_moderated = db.Column(db.Boolean, default=True)
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    member_count = db.Column(db.Integer, default=0)
    is_private = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = db.relationship('GroupMembership', back_populates='group')
    posts = db.relationship('GroupPost', back_populates='group')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'topic': self.topic,
            'member_count': self.member_count,
            'is_private': self.is_private
        }

class GroupMembership(db.Model):
    """User membership in support groups"""
    __tablename__ = 'group_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('support_groups.id'), nullable=False)
    
    role = db.Column(db.String(20), default='member')  # member, moderator
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    group = db.relationship('SupportGroup', back_populates='memberships')

class GroupPost(db.Model):
    """Posts within support groups"""
    __tablename__ = 'group_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('support_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = db.relationship('SupportGroup', back_populates='posts')

class MentalHealthArticle(db.Model):
    """Educational content articles"""
    __tablename__ = 'mental_health_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # anxiety, depression, coping
    
    # Clinical validation
    reviewed_by = db.Column(db.String(200))  # Licensed professional
    review_date = db.Column(db.Date)
    evidence_based = db.Column(db.Boolean, default=True)
    
    reading_time_minutes = db.Column(db.Integer)
    language = db.Column(db.String(20), default='en')
    
    # Trigger warnings
    trigger_warnings = db.Column(db.JSON)
    
    view_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'reading_time': self.reading_time_minutes,
            'trigger_warnings': self.trigger_warnings,
            'evidence_based': self.evidence_based,
            'language': self.language
        }