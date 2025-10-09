"""
Therapist Directory and Session Management Models
"""

from database import db
from datetime import datetime
import json

class Therapist(db.Model):
    """Professional therapist directory"""
    __tablename__ = 'therapists'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    name = db.Column(db.String(200), nullable=False)
    credentials = db.Column(db.String(200))  # PhD, LCSW, etc.
    specializations = db.Column(db.JSON)  # ["anxiety", "depression", "trauma"]
    languages = db.Column(db.JSON)  # Languages spoken
    
    # Contact information
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    location = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    
    # Service details
    gender = db.Column(db.String(20))
    accepts_insurance = db.Column(db.Boolean, default=False)
    offers_telehealth = db.Column(db.Boolean, default=True)
    cultural_competencies = db.Column(db.JSON)
    
    # Ratings and verification
    rating = db.Column(db.Float)
    review_count = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Pricing
    session_fee_min = db.Column(db.Float)
    session_fee_max = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('TherapySession', back_populates='therapist')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'credentials': self.credentials,
            'specializations': self.specializations,
            'languages': self.languages,
            'location': self.location,
            'city': self.city,
            'rating': self.rating,
            'review_count': self.review_count,
            'offers_telehealth': self.offers_telehealth,
            'session_fee_range': f"₹{self.session_fee_min}-{self.session_fee_max}" if self.session_fee_min else None
        }

class TherapySession(db.Model):
    """Therapy session bookings and tracking"""
    __tablename__ = 'therapy_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapists.id'))
    
    # Session details
    scheduled_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, default=50)  # minutes
    session_type = db.Column(db.String(50))  # video, phone, in_person
    
    # Status tracking
    status = db.Column(db.String(20))  # scheduled, completed, cancelled, no_show
    
    # Session outcomes
    pre_session_mood = db.Column(db.Integer)  # 1-10
    post_session_mood = db.Column(db.Integer)  # 1-10
    session_rating = db.Column(db.Integer)  # 1-5
    session_notes = db.Column(db.Text)  # User's private notes
    
    # Technical details
    meeting_link = db.Column(db.String(500))
    meeting_id = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='therapy_sessions')
    therapist = db.relationship('Therapist', back_populates='sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'therapist_name': self.therapist.name if self.therapist else None,
            'scheduled_time': self.scheduled_time.isoformat(),
            'duration': self.duration,
            'session_type': self.session_type,
            'status': self.status,
            'meeting_link': self.meeting_link,
            'session_rating': self.session_rating
        }