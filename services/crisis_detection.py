"""
Crisis Detection Service for WellnessWeavers
Real-time crisis detection and intervention system
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from database import db
from models.crisis import CrisisAlert, EmergencyContact
from models.user import User

class CrisisDetectionService:
    """Service for detecting crisis situations and triggering interventions"""
    
    # Crisis keywords and phrases
    CRISIS_KEYWORDS = {
        'suicidal': [
            'kill myself', 'end it all', 'not worth living', 'better off dead',
            'suicide', 'end my life', 'want to die', 'don\'t want to live',
            'self harm', 'hurt myself', 'cut myself', 'overdose'
        ],
        'self_harm': [
            'hurt myself', 'cut myself', 'self harm', 'burn myself',
            'punish myself', 'deserve pain', 'self injury'
        ],
        'substance_abuse': [
            'drink too much', 'alcohol problem', 'drug problem', 'addiction',
            'overdose', 'too many pills', 'substance abuse'
        ],
        'eating_disorder': [
            'starve myself', 'purge', 'vomit', 'eating disorder',
            'anorexia', 'bulimia', 'binge eating'
        ],
        'violence': [
            'hurt someone', 'violent thoughts', 'anger issues', 'rage',
            'lose control', 'dangerous thoughts'
        ]
    }
    
    # Risk level thresholds
    RISK_THRESHOLDS = {
        'low': 1,
        'medium': 3,
        'high': 5,
        'critical': 8
    }
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for crisis detection"""
        patterns = {}
        for category, keywords in self.CRISIS_KEYWORDS.items():
            patterns[category] = []
            for keyword in keywords:
                # Create case-insensitive pattern
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                patterns[category].append(pattern)
        return patterns
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for crisis indicators"""
        if not text:
            return {'risk_level': 'low', 'indicators': [], 'confidence': 0.0}
        
        indicators = []
        total_score = 0
        
        # Check each category
        for category, patterns in self.patterns.items():
            category_score = 0
            category_matches = []
            
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    category_score += len(matches)
                    category_matches.extend(matches)
            
            if category_score > 0:
                indicators.append({
                    'category': category,
                    'score': category_score,
                    'matches': category_matches,
                    'severity': self._get_category_severity(category, category_score)
                })
                total_score += category_score
        
        # Determine risk level
        risk_level = self._calculate_risk_level(total_score, indicators)
        confidence = min(0.95, total_score / 10.0)  # Cap confidence at 95%
        
        return {
            'risk_level': risk_level,
            'indicators': indicators,
            'confidence': confidence,
            'total_score': total_score,
            'timestamp': datetime.utcnow()
        }
    
    def _get_category_severity(self, category: str, score: int) -> str:
        """Get severity level for a category based on score"""
        if category in ['suicidal', 'self_harm']:
            if score >= 3:
                return 'critical'
            elif score >= 2:
                return 'high'
            else:
                return 'medium'
        elif category in ['substance_abuse', 'violence']:
            if score >= 2:
                return 'high'
            else:
                return 'medium'
        else:
            return 'medium'
    
    def _calculate_risk_level(self, total_score: int, indicators: List[Dict]) -> str:
        """Calculate overall risk level based on total score and indicators"""
        if total_score >= 8:
            return 'critical'
        elif total_score >= 5:
            return 'high'
        elif total_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def detect_crisis_in_conversation(self, conversation_id: int) -> Optional[CrisisAlert]:
        """Detect crisis in a specific conversation"""
        from models.conversation import Conversation
        
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return None
        
        # Analyze the conversation message
        analysis = self.analyze_text(conversation.message)
        
        if analysis['risk_level'] in ['high', 'critical']:
            # Create crisis alert
            crisis_alert = CrisisAlert(
                user_id=conversation.user_id,
                conversation_id=conversation_id,
                risk_level=analysis['risk_level'],
                crisis_indicators=analysis['indicators'],
                confidence_score=analysis['confidence'],
                detected_at=datetime.utcnow(),
                status='active'
            )
            
            db.session.add(crisis_alert)
            db.session.commit()
            
            # Trigger intervention
            self._trigger_intervention(crisis_alert)
            
            return crisis_alert
        
        return None
    
    def detect_crisis_in_mood_entry(self, mood_id: int) -> Optional[CrisisAlert]:
        """Detect crisis in a mood entry"""
        from models.mood import Mood
        
        mood = Mood.query.get(mood_id)
        if not mood or not mood.notes:
            return None
        
        # Analyze mood notes
        analysis = self.analyze_text(mood.notes)
        
        if analysis['risk_level'] in ['high', 'critical']:
            # Create crisis alert
            crisis_alert = CrisisAlert(
                user_id=mood.user_id,
                mood_entry_id=mood_id,
                risk_level=analysis['risk_level'],
                crisis_indicators=analysis['indicators'],
                confidence_score=analysis['confidence'],
                detected_at=datetime.utcnow(),
                status='active'
            )
            
            db.session.add(crisis_alert)
            db.session.commit()
            
            # Trigger intervention
            self._trigger_intervention(crisis_alert)
            
            return crisis_alert
        
        return None
    
    def _trigger_intervention(self, crisis_alert: CrisisAlert):
        """Trigger appropriate intervention based on crisis level"""
        user = User.query.get(crisis_alert.user_id)
        if not user:
            return
        
        if crisis_alert.risk_level == 'critical':
            self._trigger_critical_intervention(crisis_alert, user)
        elif crisis_alert.risk_level == 'high':
            self._trigger_high_risk_intervention(crisis_alert, user)
        else:
            self._trigger_medium_risk_intervention(crisis_alert, user)
    
    def _trigger_critical_intervention(self, crisis_alert: CrisisAlert, user: User):
        """Trigger critical intervention - immediate professional help"""
        # Update crisis alert
        crisis_alert.intervention_triggered = True
        crisis_alert.intervention_type = 'critical'
        crisis_alert.intervention_timestamp = datetime.utcnow()
        
        # Send emergency notifications
        self._send_emergency_notifications(user, crisis_alert)
        
        # Create safety plan reminder
        self._create_safety_plan_reminder(user)
        
        db.session.commit()
    
    def _trigger_high_risk_intervention(self, crisis_alert: CrisisAlert, user: User):
        """Trigger high-risk intervention - professional referral"""
        crisis_alert.intervention_triggered = True
        crisis_alert.intervention_type = 'high_risk'
        crisis_alert.intervention_timestamp = datetime.utcnow()
        
        # Send professional referral
        self._send_professional_referral(user, crisis_alert)
        
        # Create safety plan reminder
        self._create_safety_plan_reminder(user)
        
        db.session.commit()
    
    def _trigger_medium_risk_intervention(self, crisis_alert: CrisisAlert, user: User):
        """Trigger medium-risk intervention - support resources"""
        crisis_alert.intervention_triggered = True
        crisis_alert.intervention_type = 'medium_risk'
        crisis_alert.intervention_timestamp = datetime.utcnow()
        
        # Send support resources
        self._send_support_resources(user, crisis_alert)
        
        db.session.commit()
    
    def _send_emergency_notifications(self, user: User, crisis_alert: CrisisAlert):
        """Send emergency notifications to contacts"""
        # Get emergency contacts
        emergency_contacts = EmergencyContact.query.filter_by(
            user_id=user.id,
            is_primary=True
        ).all()
        
        for contact in emergency_contacts:
            # In a real implementation, send SMS/email notifications
            print(f"EMERGENCY ALERT: {user.full_name} needs immediate help!")
            print(f"Contact: {contact.name} - {contact.phone_number}")
            print(f"Risk Level: {crisis_alert.risk_level}")
    
    def _send_professional_referral(self, user: User, crisis_alert: CrisisAlert):
        """Send professional referral information"""
        # In a real implementation, send professional referral
        print(f"Professional referral sent for {user.full_name}")
        print(f"Risk Level: {crisis_alert.risk_level}")
    
    def _send_support_resources(self, user: User, crisis_alert: CrisisAlert):
        """Send support resources"""
        # In a real implementation, send support resources
        print(f"Support resources sent for {user.full_name}")
        print(f"Risk Level: {crisis_alert.risk_level}")
    
    def _create_safety_plan_reminder(self, user: User):
        """Create safety plan reminder"""
        # In a real implementation, create safety plan reminder
        print(f"Safety plan reminder created for {user.full_name}")
    
    def get_user_crisis_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user's crisis history"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        crisis_alerts = CrisisAlert.query.filter(
            CrisisAlert.user_id == user_id,
            CrisisAlert.detected_at >= start_date
        ).order_by(CrisisAlert.detected_at.desc()).all()
        
        return [alert.to_dict() for alert in crisis_alerts]
    
    def get_crisis_statistics(self, user_id: int) -> Dict:
        """Get crisis statistics for a user"""
        crisis_alerts = CrisisAlert.query.filter_by(user_id=user_id).all()
        
        if not crisis_alerts:
            return {
                'total_alerts': 0,
                'risk_distribution': {},
                'intervention_rate': 0,
                'recent_trend': 'stable'
            }
        
        # Calculate statistics
        total_alerts = len(crisis_alerts)
        risk_distribution = {}
        interventions = 0
        
        for alert in crisis_alerts:
            risk_distribution[alert.risk_level] = risk_distribution.get(alert.risk_level, 0) + 1
            if alert.intervention_triggered:
                interventions += 1
        
        intervention_rate = (interventions / total_alerts) * 100 if total_alerts > 0 else 0
        
        # Calculate recent trend
        recent_alerts = [alert for alert in crisis_alerts 
                        if alert.detected_at >= datetime.utcnow() - timedelta(days=7)]
        older_alerts = [alert for alert in crisis_alerts 
                       if alert.detected_at < datetime.utcnow() - timedelta(days=7)]
        
        if len(recent_alerts) > len(older_alerts):
            recent_trend = 'increasing'
        elif len(recent_alerts) < len(older_alerts):
            recent_trend = 'decreasing'
        else:
            recent_trend = 'stable'
        
        return {
            'total_alerts': total_alerts,
            'risk_distribution': risk_distribution,
            'intervention_rate': intervention_rate,
            'recent_trend': recent_trend
        }

# Global instance
crisis_detection_service = CrisisDetectionService()
