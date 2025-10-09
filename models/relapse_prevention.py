"""
Relapse Prevention Model for WellnessWeavers
Track recovery patterns and early warning signs
"""

from database import db
from datetime import datetime, date, timedelta
import json

class RelapsePrevention(db.Model):
    """Track recovery from depression/anxiety episodes"""
    __tablename__ = 'relapse_prevention'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Recovery tracking
    days_stable = db.Column(db.Integer, default=0)  # Days since last episode
    last_episode_date = db.Column(db.Date)
    episode_type = db.Column(db.String(50))  # depression, anxiety, mixed
    episode_severity = db.Column(db.String(20))  # mild, moderate, severe
    
    # Personal warning signs (user-specific)
    personal_warning_signs = db.Column(db.JSON)  # Sleep changes, isolation, etc.
    warning_sign_frequency = db.Column(db.JSON)  # How often each sign appears
    
    # What worked before (user's effective interventions)
    effective_interventions = db.Column(db.JSON)  # What helped in past episodes
    intervention_effectiveness = db.Column(db.JSON)  # How well each worked
    
    # High-risk situations and triggers
    triggers_map = db.Column(db.JSON)  # Situations that trigger episodes
    trigger_severity = db.Column(db.JSON)  # How severe each trigger is
    
    # Recovery milestones and goals
    recovery_milestones = db.Column(db.JSON)  # Personal recovery goals
    milestone_progress = db.Column(db.JSON)  # Progress on each milestone
    
    # Support system
    support_people = db.Column(db.JSON)  # Who to contact for help
    support_roles = db.Column(db.JSON)  # What each person can help with
    professional_contacts = db.Column(db.JSON)  # Therapists, doctors, etc.
    
    # Cultural and family factors (important for Indian users)
    family_expectations = db.Column(db.JSON)  # Family pressure points
    cultural_stressors = db.Column(db.JSON)  # Cultural factors affecting mental health
    academic_pressure = db.Column(db.JSON)  # Academic stress factors
    social_stigma_concerns = db.Column(db.JSON)  # Stigma-related stressors
    
    # Early intervention plan
    early_intervention_steps = db.Column(db.JSON)  # What to do when warning signs appear
    crisis_plan = db.Column(db.JSON)  # What to do in crisis
    professional_help_triggers = db.Column(db.JSON)  # When to seek professional help
    
    # Monitoring and alerts
    monitoring_frequency = db.Column(db.String(20), default='daily')  # How often to check
    alert_threshold = db.Column(db.Integer, default=3)  # Warning signs before alert
    last_check_date = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    monitoring_enabled = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super(RelapsePrevention, self).__init__(**kwargs)
        # Initialize with common warning signs
        if not self.personal_warning_signs:
            self.personal_warning_signs = [
                "Sleep changes (too much or too little)",
                "Loss of appetite or overeating",
                "Withdrawing from friends and family",
                "Loss of interest in activities",
                "Feeling hopeless or worthless",
                "Increased irritability or anger",
                "Difficulty concentrating",
                "Physical symptoms (headaches, stomachaches)",
                "Increased alcohol or drug use",
                "Thoughts of self-harm"
            ]
    
    def update_stability(self):
        """Update days stable and check for warning signs"""
        if self.last_episode_date:
            self.days_stable = (date.today() - self.last_episode_date).days
        else:
            self.days_stable = 0
        
        self.last_check_date = date.today()
        db.session.commit()
    
    def add_warning_sign(self, sign: str, severity: int = 1):
        """Add a warning sign occurrence"""
        if not self.warning_sign_frequency:
            self.warning_sign_frequency = {}
        
        if sign not in self.warning_sign_frequency:
            self.warning_sign_frequency[sign] = []
        
        self.warning_sign_frequency[sign].append({
            'date': date.today().isoformat(),
            'severity': severity
        })
        
        # Check if alert threshold is reached
        recent_signs = [s for s in self.warning_sign_frequency[sign] 
                       if datetime.fromisoformat(s['date']).date() >= date.today() - timedelta(days=7)]
        
        if len(recent_signs) >= self.alert_threshold:
            return self.trigger_early_intervention(sign)
        
        return False
    
    def trigger_early_intervention(self, trigger_sign: str):
        """Trigger early intervention when warning signs appear"""
        # This would integrate with notification service
        intervention_data = {
            'trigger_sign': trigger_sign,
            'days_stable': self.days_stable,
            'intervention_steps': self.early_intervention_steps,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Return intervention data for notification service
        return intervention_data
    
    def get_risk_level(self):
        """Calculate current risk level based on warning signs"""
        if not self.warning_sign_frequency:
            return 'low'
        
        # Count recent warning signs (last 7 days)
        recent_count = 0
        for sign, occurrences in self.warning_sign_frequency.items():
            recent_occurrences = [o for o in occurrences 
                                if datetime.fromisoformat(o['date']).date() >= date.today() - timedelta(days=7)]
            recent_count += len(recent_occurrences)
        
        if recent_count >= 5:
            return 'high'
        elif recent_count >= 3:
            return 'medium'
        else:
            return 'low'
    
    def get_recovery_insights(self):
        """Generate insights about recovery patterns"""
        insights = []
        
        # Stability insights
        if self.days_stable >= 30:
            insights.append({
                'type': 'positive',
                'message': f'Great job! You\'ve been stable for {self.days_stable} days.',
                'suggestion': 'Continue your current strategies.'
            })
        elif self.days_stable < 7:
            insights.append({
                'type': 'concern',
                'message': 'You\'re in early recovery. Be extra gentle with yourself.',
                'suggestion': 'Focus on basic self-care and reach out for support.'
            })
        
        # Warning sign insights
        if self.warning_sign_frequency:
            most_common = max(self.warning_sign_frequency.items(), 
                            key=lambda x: len(x[1]))
            insights.append({
                'type': 'info',
                'message': f'Your most common warning sign is: {most_common[0]}',
                'suggestion': 'Consider developing specific coping strategies for this.'
            })
        
        # Trigger insights
        if self.triggers_map:
            high_risk_triggers = [t for t, s in self.triggers_map.items() if s >= 7]
            if high_risk_triggers:
                insights.append({
                    'type': 'warning',
                    'message': f'High-risk triggers identified: {", ".join(high_risk_triggers)}',
                    'suggestion': 'Develop specific plans for these situations.'
                })
        
        return insights
    
    def create_intervention_plan(self):
        """Create personalized intervention plan"""
        plan = {
            'early_warning_signs': self.personal_warning_signs,
            'immediate_actions': [],
            'support_contacts': self.support_people,
            'professional_help': self.professional_contacts,
            'coping_strategies': self.effective_interventions,
            'cultural_considerations': {
                'family_expectations': self.family_expectations,
                'academic_pressure': self.academic_pressure,
                'stigma_concerns': self.social_stigma_concerns
            }
        }
        
        # Add immediate actions based on risk level
        risk_level = self.get_risk_level()
        
        if risk_level == 'high':
            plan['immediate_actions'] = [
                'Contact your therapist or doctor immediately',
                'Reach out to a trusted friend or family member',
                'Use your crisis plan',
                'Consider going to a safe place'
            ]
        elif risk_level == 'medium':
            plan['immediate_actions'] = [
                'Use your coping strategies',
                'Reach out to your support system',
                'Consider scheduling a therapy appointment',
                'Practice self-care activities'
            ]
        else:
            plan['immediate_actions'] = [
                'Continue your current strategies',
                'Stay connected with your support system',
                'Monitor your warning signs',
                'Practice preventive self-care'
            ]
        
        return plan
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'days_stable': self.days_stable,
            'last_episode_date': self.last_episode_date.isoformat() if self.last_episode_date else None,
            'episode_type': self.episode_type,
            'episode_severity': self.episode_severity,
            'personal_warning_signs': self.personal_warning_signs,
            'warning_sign_frequency': self.warning_sign_frequency,
            'effective_interventions': self.effective_interventions,
            'triggers_map': self.triggers_map,
            'recovery_milestones': self.recovery_milestones,
            'support_people': self.support_people,
            'professional_contacts': self.professional_contacts,
            'family_expectations': self.family_expectations,
            'cultural_stressors': self.cultural_stressors,
            'academic_pressure': self.academic_pressure,
            'social_stigma_concerns': self.social_stigma_concerns,
            'early_intervention_steps': self.early_intervention_steps,
            'crisis_plan': self.crisis_plan,
            'risk_level': self.get_risk_level(),
            'insights': self.get_recovery_insights(),
            'intervention_plan': self.create_intervention_plan(),
            'is_active': self.is_active,
            'monitoring_enabled': self.monitoring_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_progress(cls, user_id):
        """Get user's relapse prevention progress"""
        prevention = cls.query.filter_by(user_id=user_id, is_active=True).first()
        
        if not prevention:
            return {
                'has_plan': False,
                'message': 'No relapse prevention plan found. Consider creating one.'
            }
        
        return {
            'has_plan': True,
            'days_stable': prevention.days_stable,
            'risk_level': prevention.get_risk_level(),
            'insights': prevention.get_recovery_insights(),
            'intervention_plan': prevention.create_intervention_plan()
        }
    
    def __repr__(self):
        return f'<RelapsePrevention {self.id}: {self.days_stable} days stable>'
