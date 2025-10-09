"""
Crisis Support Models for WellnessWeavers
Emergency detection, intervention, and safety planning
"""

from database import db
from datetime import datetime
import json

class CrisisAlert(db.Model):
    """Crisis alerts with comprehensive intervention tracking"""
    __tablename__ = 'crisis_alerts'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Alert classification
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    trigger_source = db.Column(db.String(50))  # mood, conversation, voice_journal, manual, pattern
    alert_type = db.Column(db.String(50), default='general')  # suicide, self_harm, substance, etc.
    
    # Detection details
    indicators = db.Column(db.JSON)  # Specific crisis indicators detected
    confidence_score = db.Column(db.Float)  # AI confidence in detection (0-1)
    context = db.Column(db.Text)  # Context where alert was triggered
    
    # Risk assessment
    risk_factors = db.Column(db.JSON)  # Identified risk factors
    protective_factors = db.Column(db.JSON)  # Identified protective factors
    immediate_danger = db.Column(db.Boolean, default=False)  # Immediate threat to life
    
    # User state at time of alert
    user_location = db.Column(db.String(200))  # If available
    time_of_day = db.Column(db.String(20))
    recent_stressors = db.Column(db.JSON)  # Recent identified stressors
    support_system_available = db.Column(db.Boolean)  # Are supports reachable
    
    # Response and intervention
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved, escalated
    intervention_attempted = db.Column(db.Boolean, default=False)
    intervention_type = db.Column(db.String(50))  # ai_support, human_chat, professional_referral
    intervention_effective = db.Column(db.Boolean)  # Was intervention helpful
    
    # Professional involvement
    professional_contacted = db.Column(db.Boolean, default=False)
    professional_type = db.Column(db.String(50))  # therapist, crisis_counselor, emergency
    professional_response_time = db.Column(db.Integer)  # Minutes to respond
    
    # Emergency contacts
    emergency_contact_notified = db.Column(db.Boolean, default=False)
    contacts_notified = db.Column(db.JSON)  # List of contacts reached out to
    
    # Follow-up and resolution
    follow_up_scheduled = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    user_feedback = db.Column(db.Text)  # How user felt about response
    
    # Learning and improvement
    false_positive = db.Column(db.Boolean)  # Was this a false alarm
    improvement_suggestions = db.Column(db.JSON)  # How to improve detection
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = db.Column(db.DateTime)  # When user/professional acknowledged
    resolved_at = db.Column(db.DateTime)  # When crisis was resolved
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='crisis_alerts')
    
    def initiate_intervention_protocol(self):
        """Start appropriate intervention based on severity"""
        intervention_steps = []
        
        if self.severity == 'critical':
            intervention_steps.extend([
                self._provide_immediate_crisis_resources(),
                self._attempt_professional_contact(),
                self._notify_emergency_contacts(),
                self._suggest_emergency_services()
            ])
        elif self.severity == 'high':
            intervention_steps.extend([
                self._provide_crisis_resources(),
                self._schedule_professional_contact(),
                self._activate_safety_plan(),
                self._notify_emergency_contacts()
            ])
        elif self.severity == 'medium':
            intervention_steps.extend([
                self._provide_support_resources(),
                self._suggest_coping_strategies(),
                self._check_safety_plan(),
                self._schedule_check_in()
            ])
        else:  # low
            intervention_steps.extend([
                self._provide_self_help_resources(),
                self._suggest_wellness_activities(),
                self._monitor_for_escalation()
            ])
        
        self.intervention_attempted = True
        self.intervention_type = f'protocol_{self.severity}'
        
        return intervention_steps
    
    def _provide_immediate_crisis_resources(self):
        """Provide immediate crisis intervention resources"""
        return {
            'type': 'immediate_resources',
            'title': 'Immediate Help Available',
            'resources': [
                {
                    'name': 'National Suicide Prevention Lifeline',
                    'phone': '988',
                    'description': '24/7 crisis counseling'
                },
                {
                    'name': 'Crisis Text Line',
                    'contact': 'Text HOME to 741741',
                    'description': 'Free 24/7 crisis support via text'
                },
                {
                    'name': 'Vandrevala Foundation (India)',
                    'phone': '1860 266 2345',
                    'description': '24/7 crisis helpline for India'
                }
            ]
        }
    
    def _provide_crisis_resources(self):
        """Provide crisis support resources"""
        return {
            'type': 'crisis_resources',
            'title': 'Crisis Support Available',
            'resources': [
                {
                    'name': 'iCall',
                    'phone': '022-25563291',
                    'description': 'Counseling helpline (Mon-Sat, 8AM-10PM)'
                },
                {
                    'name': 'AASRA',
                    'phone': '022-27546669',
                    'description': '24/7 suicide prevention helpline'
                },
                {
                    'name': 'Sneha',
                    'phone': '044-24640050',
                    'description': 'Chennai-based crisis helpline'
                }
            ],
            'immediate_actions': [
                'Reach out to someone you trust',
                'Remove access to means of self-harm',
                'Stay with supportive people',
                'Call a crisis hotline'
            ]
        }
    
    def _activate_safety_plan(self):
        """Activate user's safety plan if available"""
        from models.safe_features import SafetyPlan
        
        safety_plan = SafetyPlan.query.filter_by(user_id=self.user_id).first()
        
        if safety_plan:
            safety_plan.times_accessed_in_crisis += 1
            db.session.commit()
            
            return {
                'type': 'safety_plan_activation',
                'title': 'Your Safety Plan',
                'plan': safety_plan.to_dict()
            }
        else:
            return {
                'type': 'safety_plan_creation',
                'title': 'Create Your Safety Plan',
                'message': 'Let\'s create a personalized safety plan for future crises',
                'action': 'create_safety_plan'
            }
    
    def _notify_emergency_contacts(self):
        """Notify user's emergency contacts"""
        contacts = EmergencyContact.query.filter_by(
            user_id=self.user_id,
            notify_on_crisis=True
        ).order_by(EmergencyContact.priority).all()
        
        if not contacts:
            return {
                'type': 'no_emergency_contacts',
                'message': 'No emergency contacts configured',
                'action': 'add_emergency_contacts'
            }
        
        # In a real implementation, this would send notifications
        self.emergency_contact_notified = True
        self.contacts_notified = [
            {'name': contact.name, 'relationship': contact.relationship}
            for contact in contacts
        ]
        
        return {
            'type': 'emergency_contacts_notified',
            'title': 'Emergency Contacts Notified',
            'contacts': self.contacts_notified,
            'message': f'Notified {len(contacts)} emergency contacts'
        }
    
    def _suggest_emergency_services(self):
        """Suggest contacting emergency services"""
        return {
            'type': 'emergency_services',
            'title': 'Emergency Services',
            'message': 'If you are in immediate danger, please call:',
            'services': [
                {
                    'name': 'Emergency (India)',
                    'number': '112',
                    'description': 'National emergency number'
                },
                {
                    'name': 'Police',
                    'number': '100',
                    'description': 'Police emergency'
                },
                {
                    'name': 'Medical Emergency',
                    'number': '108',
                    'description': 'Ambulance and medical emergency'
                }
            ]
        }
    
    def get_crisis_summary(self):
        """Generate a summary of the crisis situation"""
        return {
            'id': self.id,
            'severity': self.severity,
            'trigger_source': self.trigger_source,
            'indicators': self.indicators,
            'status': self.status,
            'intervention_attempted': self.intervention_attempted,
            'professional_contacted': self.professional_contacted,
            'emergency_contact_notified': self.emergency_contact_notified,
            'created_at': self.created_at.isoformat(),
            'time_to_resolution': self._calculate_resolution_time()
        }
    
    def _calculate_resolution_time(self):
        """Calculate time from alert to resolution"""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return {
                'minutes': int(delta.total_seconds() / 60),
                'hours': round(delta.total_seconds() / 3600, 1)
            }
        return None
    
    def mark_resolved(self, resolution_notes='', user_feedback=''):
        """Mark the crisis as resolved"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = resolution_notes
        self.user_feedback = user_feedback
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary representation"""
        alert_dict = {
            'id': self.id,
            'severity': self.severity,
            'trigger_source': self.trigger_source,
            'status': self.status,
            'intervention_attempted': self.intervention_attempted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
        
        if include_sensitive:
            alert_dict.update({
                'indicators': self.indicators,
                'context': self.context,
                'risk_factors': self.risk_factors,
                'professional_contacted': self.professional_contacted,
                'emergency_contact_notified': self.emergency_contact_notified,
                'resolution_notes': self.resolution_notes,
                'user_feedback': self.user_feedback
            })
        
        return alert_dict
    
    def __repr__(self):
        return f'<CrisisAlert {self.id}: {self.severity} - {self.status}>'


class EmergencyContact(db.Model):
    """User's emergency contacts for crisis situations"""
    __tablename__ = 'emergency_contacts'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contact information
    name = db.Column(db.String(200), nullable=False)
    relationship = db.Column(db.String(100))  # parent, sibling, friend, therapist, etc.
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    alternate_phone = db.Column(db.String(20))
    
    # Contact preferences
    priority = db.Column(db.Integer, default=1)  # 1=primary, 2=secondary, etc.
    preferred_method = db.Column(db.String(20), default='phone')  # phone, email, text
    time_restrictions = db.Column(db.JSON)  # When they can be contacted
    
    # Crisis settings
    notify_on_crisis = db.Column(db.Boolean, default=True)
    notify_on_high_risk_only = db.Column(db.Boolean, default=False)
    can_provide_immediate_support = db.Column(db.Boolean, default=True)
    
    # Contact context
    knows_about_mental_health = db.Column(db.Boolean, default=True)
    supportive_relationship = db.Column(db.Boolean, default=True)
    geographic_proximity = db.Column(db.String(50))  # same_city, same_state, different_state
    
    # Usage tracking
    times_contacted = db.Column(db.Integer, default=0)
    last_contacted = db.Column(db.DateTime)
    response_rate = db.Column(db.Float)  # How often they respond when contacted
    average_response_time_minutes = db.Column(db.Integer)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    verified = db.Column(db.Boolean, default=False)  # Has contact confirmed they're willing
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='emergency_contacts')
    
    def send_crisis_notification(self, crisis_alert):
        """Send crisis notification to this contact"""
        # In a real implementation, this would send actual notifications
        notification_data = {
            'contact_name': self.name,
            'user_name': crisis_alert.user.full_name or crisis_alert.user.username,
            'severity': crisis_alert.severity,
            'message': self._generate_crisis_message(crisis_alert),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Update usage tracking
        self.times_contacted += 1
        self.last_contacted = datetime.utcnow()
        
        return notification_data
    
    def _generate_crisis_message(self, crisis_alert):
        """Generate appropriate crisis notification message"""
        user_name = crisis_alert.user.full_name or crisis_alert.user.username
        
        if crisis_alert.severity == 'critical':
            return f"URGENT: {user_name} may be in crisis and needs immediate support. Please reach out to them right away. If you believe they are in immediate danger, please contact emergency services."
        elif crisis_alert.severity == 'high':
            return f"IMPORTANT: {user_name} is going through a difficult time and may need support. Please consider reaching out to check on them when you can."
        else:
            return f"FYI: {user_name} has been struggling recently. A caring message or check-in would be appreciated when you have a moment."
    
    def check_availability(self):
        """Check if contact is available based on time restrictions"""
        if not self.time_restrictions:
            return True
        
        current_hour = datetime.now().hour
        current_day = datetime.now().strftime('%A').lower()
        
        # Check time restrictions
        if 'hours' in self.time_restrictions:
            allowed_hours = self.time_restrictions['hours']
            if current_hour < allowed_hours.get('start', 0) or current_hour > allowed_hours.get('end', 23):
                return False
        
        # Check day restrictions
        if 'days' in self.time_restrictions:
            allowed_days = self.time_restrictions['days']
            if current_day not in [day.lower() for day in allowed_days]:
                return False
        
        return True
    
    def get_contact_score(self):
        """Calculate effectiveness score for this contact"""
        score = 0
        
        # Priority bonus (lower numbers = higher priority = higher score)
        score += max(0, 5 - self.priority)
        
        # Response rate
        if self.response_rate:
            score += self.response_rate * 3
        
        # Response speed
        if self.average_response_time_minutes:
            if self.average_response_time_minutes <= 30:
                score += 3
            elif self.average_response_time_minutes <= 120:
                score += 2
            else:
                score += 1
        
        # Relationship factors
        if self.supportive_relationship:
            score += 2
        if self.knows_about_mental_health:
            score += 2
        if self.can_provide_immediate_support:
            score += 2
        
        # Geographic proximity
        if self.geographic_proximity == 'same_city':
            score += 2
        elif self.geographic_proximity == 'same_state':
            score += 1
        
        # Availability
        if self.check_availability():
            score += 1
        
        return min(20, score)  # Cap at 20
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary representation"""
        contact_dict = {
            'id': self.id,
            'name': self.name,
            'relationship': self.relationship,
            'priority': self.priority,
            'preferred_method': self.preferred_method,
            'notify_on_crisis': self.notify_on_crisis,
            'is_active': self.is_active,
            'verified': self.verified
        }
        
        if include_sensitive:
            contact_dict.update({
                'phone': self.phone,
                'email': self.email,
                'times_contacted': self.times_contacted,
                'response_rate': self.response_rate,
                'contact_score': self.get_contact_score()
            })
        
        return contact_dict
    
    def __repr__(self):
        return f'<EmergencyContact {self.name} ({self.relationship}) - Priority {self.priority}>'