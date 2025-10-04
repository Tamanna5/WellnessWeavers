"""
Goals and Milestones Models
"""

from app import db
from datetime import datetime, date
import json

class Goal(db.Model):
    """User goals with milestone tracking"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # mood, habits, relationships, etc.
    
    target_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, completed, paused, cancelled
    progress_percentage = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='goals')
    milestones = db.relationship('Milestone', back_populates='goal', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'progress_percentage': self.progress_percentage,
            'status': self.status,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'milestones': [m.to_dict() for m in self.milestones]
        }

class Milestone(db.Model):
    """Individual milestones for goals"""
    __tablename__ = 'milestones'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    order = db.Column(db.Integer)
    
    # Relationships
    goal = db.relationship('Goal', back_populates='milestones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'order': self.order
        }