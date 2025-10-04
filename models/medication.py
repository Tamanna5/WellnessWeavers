"""
Medication Tracking Models for WellnessWeavers
Safe medication management and adherence tracking
"""

from app import db
from datetime import datetime, date, timedelta
import json

class Medication(db.Model):
    """Medication tracking with adherence monitoring"""
    __tablename__ = 'medications'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Medication details
    name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))  # "10mg", "1 tablet"
    frequency = db.Column(db.String(100))  # "twice daily", "as needed"
    time_of_day = db.Column(db.JSON)  # ["09:00", "21:00"]
    
    # Prescription information
    prescribing_doctor = db.Column(db.String(200))
    doctor_contact = db.Column(db.String(200))
    purpose = db.Column(db.Text)  # What condition it treats
    
    # Scheduling
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Reminders
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_advance_minutes = db.Column(db.Integer, default=15)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='medications')
    logs = db.relationship('MedicationLog', back_populates='medication', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_adherence_rate(self, days=30):
        """Calculate medication adherence rate"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get expected doses (simplified - assumes daily frequency)
        expected_doses = days if self.frequency else 0
        
        # Get actual logs
        taken_count = self.logs.filter(
            MedicationLog.scheduled_date >= start_date,
            MedicationLog.taken == True
        ).count()
        
        if expected_doses == 0:
            return 0.0
        
        return min(100.0, (taken_count / expected_doses) * 100)
    
    def to_dict(self, include_analytics=False):
        """Convert to dictionary"""
        med_dict = {
            'id': self.id,
            'name': self.name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'time_of_day': self.time_of_day,
            'purpose': self.purpose,
            'is_active': self.is_active,
            'reminder_enabled': self.reminder_enabled
        }
        
        if include_analytics:
            med_dict.update({
                'adherence_rate_30d': self.calculate_adherence_rate(30),
                'last_taken': self.get_last_taken_date()
            })
        
        return med_dict
    
    def get_last_taken_date(self):
        """Get date medication was last taken"""
        last_log = self.logs.filter_by(taken=True).order_by(MedicationLog.scheduled_date.desc()).first()
        return last_log.scheduled_date.isoformat() if last_log else None

class MedicationLog(db.Model):
    """Individual medication doses tracking"""
    __tablename__ = 'medication_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    
    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time)
    actual_time = db.Column(db.DateTime)
    
    # Tracking
    taken = db.Column(db.Boolean, nullable=False, default=False)
    missed_reason = db.Column(db.String(200))  # If not taken
    
    # Effects tracking
    side_effects = db.Column(db.JSON)
    effectiveness_rating = db.Column(db.Integer)  # 1-5
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    medication = db.relationship('Medication', back_populates='logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'scheduled_date': self.scheduled_date.isoformat(),
            'taken': self.taken,
            'actual_time': self.actual_time.isoformat() if self.actual_time else None,
            'effectiveness_rating': self.effectiveness_rating,
            'side_effects': self.side_effects,
            'notes': self.notes
        }