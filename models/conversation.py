"""
Conversation Model for WellnessWeavers
AI Chat interactions with comprehensive analysis and context tracking
"""

from app import db
from datetime import datetime
import json

class Conversation(db.Model):
    """Enhanced Conversation model for AI chat interactions"""
    __tablename__ = 'conversations'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), index=True)  # Group related messages
    
    # Message content
    message = db.Column(db.Text, nullable=False)  # User's message
    response = db.Column(db.Text)  # AI's response
    message_type = db.Column(db.String(20), default='text')  # text, voice, image
    
    # Conversation context
    conversation_context = db.Column(db.JSON)  # Previous context for AI
    user_intent = db.Column(db.String(100))  # What user is trying to do
    topic = db.Column(db.String(100))  # Main topic discussed
    conversation_stage = db.Column(db.String(50))  # greeting, problem-solving, wrap-up
    
    # Language and cultural context
    language_detected = db.Column(db.String(10))
    cultural_context = db.Column(db.JSON)  # Cultural references mentioned
    code_switching = db.Column(db.Boolean, default=False)  # Mixed languages
    
    # AI Analysis
    sentiment = db.Column(db.String(20))  # positive, negative, neutral
    sentiment_score = db.Column(db.Float)  # -1.0 to 1.0
    emotion_analysis = db.Column(db.JSON)  # Multiple emotions detected
    confidence_score = db.Column(db.Float)  # AI confidence in understanding
    
    # Crisis and risk detection
    crisis_indicators = db.Column(db.JSON)  # Crisis keywords/phrases detected
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    intervention_triggered = db.Column(db.Boolean, default=False)
    professional_referral_made = db.Column(db.Boolean, default=False)
    
    # Therapeutic elements
    therapeutic_technique = db.Column(db.String(50))  # CBT, DBT, mindfulness, etc.
    coping_strategies_suggested = db.Column(db.JSON)
    user_receptiveness = db.Column(db.Integer)  # 1-5 how receptive user was
    homework_assigned = db.Column(db.JSON)  # Tasks suggested to user
    
    # Conversation quality
    user_satisfaction = db.Column(db.Integer)  # 1-5 rating from user
    ai_helpfulness = db.Column(db.Integer)  # 1-5 how helpful AI was
    conversation_completed = db.Column(db.Boolean, default=False)
    follow_up_needed = db.Column(db.Boolean, default=False)
    
    # Performance metrics
    response_time_ms = db.Column(db.Integer)  # AI response time
    message_length = db.Column(db.Integer)  # Character count of message
    response_length = db.Column(db.Integer)  # Character count of response
    
    # Privacy and moderation
    contains_sensitive_info = db.Column(db.Boolean, default=False)
    flagged_for_review = db.Column(db.Boolean, default=False)
    reviewed_by_human = db.Column(db.Boolean, default=False)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    analyzed_at = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='conversations')
    
    def analyze_conversation(self, ai_service):
        """Analyze conversation with AI services"""
        try:
            # Basic sentiment analysis
            sentiment_data = ai_service.analyze_sentiment(self.message)
            self.sentiment = sentiment_data.get('sentiment', 'neutral')
            self.sentiment_score = sentiment_data.get('score', 0.0)
            
            # Emotion analysis
            emotions = ai_service.analyze_emotions(self.message)
            self.emotion_analysis = emotions
            
            # Language detection
            self.language_detected = ai_service.detect_language(self.message)
            
            # Crisis detection
            crisis_data = ai_service.detect_crisis_indicators(self.message)
            self.crisis_indicators = crisis_data.get('indicators', [])
            self.risk_level = crisis_data.get('risk_level', 'low')
            
            if self.risk_level in ['high', 'critical']:
                self.intervention_triggered = True
                self.flag_for_intervention()
            
            # Intent analysis
            self.user_intent = ai_service.analyze_intent(self.message)
            
            # Topic extraction
            self.topic = ai_service.extract_main_topic(self.message)
            
            # Code-switching detection (multiple languages)
            self.code_switching = ai_service.detect_code_switching(self.message)
            
            # Cultural context
            cultural_refs = ai_service.extract_cultural_context(self.message)
            self.cultural_context = cultural_refs
            
            self.analyzed_at = datetime.utcnow()
            
        except Exception as e:
            print(f"Conversation analysis failed for {self.id}: {str(e)}")
    
    def flag_for_intervention(self):
        """Flag conversation for human intervention"""
        self.flagged_for_review = True
        
        # Create crisis alert if not exists
        from models.crisis import CrisisAlert
        
        existing_alert = CrisisAlert.query.filter(
            CrisisAlert.user_id == self.user_id,
            CrisisAlert.status == 'active',
            CrisisAlert.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).first()
        
        if not existing_alert:
            alert = CrisisAlert(
                user_id=self.user_id,
                severity=self.risk_level,
                trigger_source='conversation',
                context=self.message[:500],  # First 500 chars for context
                indicators=self.crisis_indicators
            )
            db.session.add(alert)
    
    def generate_contextual_response(self, ai_service, user_profile):
        """Generate AI response considering user context"""
        try:
            # Prepare context for AI
            context = {
                'user_profile': user_profile,
                'conversation_history': self.get_recent_context(),
                'current_mood': self.get_user_current_mood(),
                'cultural_background': user_profile.get('cultural_background'),
                'preferred_language': user_profile.get('preferred_language', 'en'),
                'ai_personality': user_profile.get('ai_companion_personality', 'supportive_friend'),
                'therapy_preferences': user_profile.get('therapy_preferences', []),
                'risk_level': self.risk_level
            }
            
            # Generate response
            response_data = ai_service.generate_contextual_response(
                message=self.message,
                context=context
            )
            
            self.response = response_data.get('response')
            self.therapeutic_technique = response_data.get('technique_used')
            self.coping_strategies_suggested = response_data.get('coping_strategies')
            self.homework_assigned = response_data.get('homework')
            self.professional_referral_made = response_data.get('referral_made', False)
            
            # Update conversation stage
            self.conversation_stage = response_data.get('stage', 'ongoing')
            
            return self.response
            
        except Exception as e:
            print(f"Response generation failed for {self.id}: {str(e)}")
            return "I'm here to listen and support you. Could you tell me more about how you're feeling?"
    
    def get_recent_context(self, limit=5):
        """Get recent conversation context for AI"""
        recent_conversations = Conversation.query.filter(
            Conversation.user_id == self.user_id,
            Conversation.session_id == self.session_id,
            Conversation.id < self.id
        ).order_by(Conversation.timestamp.desc()).limit(limit).all()
        
        context = []
        for conv in reversed(recent_conversations):  # Chronological order
            context.append({
                'message': conv.message,
                'response': conv.response,
                'sentiment': conv.sentiment,
                'topic': conv.topic
            })
        
        return context
    
    def get_user_current_mood(self):
        """Get user's most recent mood for context"""
        from models.mood import Mood
        
        recent_mood = Mood.query.filter_by(user_id=self.user_id)\
            .order_by(Mood.timestamp.desc()).first()
        
        if recent_mood:
            return {
                'score': recent_mood.mood_score,
                'emotion': recent_mood.emotion,
                'timestamp': recent_mood.timestamp.isoformat()
            }
        return None
    
    def calculate_conversation_value(self):
        """Calculate the therapeutic value of this conversation"""
        value_score = 0
        
        # Length bonus (meaningful conversations)
        if self.message_length > 50:
            value_score += 2
        if self.message_length > 200:
            value_score += 3
        
        # Emotional openness
        if self.emotion_analysis:
            emotion_count = len(self.emotion_analysis)
            value_score += min(5, emotion_count)
        
        # Coping strategies
        if self.coping_strategies_suggested:
            value_score += len(self.coping_strategies_suggested) * 2
        
        # User receptiveness
        if self.user_receptiveness:
            value_score += self.user_receptiveness
        
        # Crisis intervention (negative value but important)
        if self.intervention_triggered:
            value_score += 10  # High value for safety
        
        return min(20, value_score)  # Cap at 20
    
    def get_conversation_insights(self):
        """Generate insights about this conversation"""
        insights = []
        
        # Sentiment insights
        if self.sentiment_score < -0.5:
            insights.append({
                'type': 'concern',
                'message': 'User expressed negative emotions',
                'recommendation': 'Consider follow-up or additional support'
            })
        elif self.sentiment_score > 0.5:
            insights.append({
                'type': 'positive',
                'message': 'User showed positive engagement',
                'recommendation': 'Reinforce positive patterns'
            })
        
        # Crisis insights
        if self.crisis_indicators:
            insights.append({
                'type': 'urgent',
                'message': f'Crisis indicators detected: {", ".join(self.crisis_indicators[:3])}',
                'recommendation': 'Immediate intervention required'
            })
        
        # Cultural insights
        if self.cultural_context:
            insights.append({
                'type': 'cultural',
                'message': 'Cultural context detected',
                'recommendation': 'Tailor responses to cultural background'
            })
        
        # Code-switching insights
        if self.code_switching:
            insights.append({
                'type': 'linguistic',
                'message': 'User switching between languages',
                'recommendation': 'Adapt to user\'s natural communication style'
            })
        
        return insights
    
    def to_dict(self, include_analysis=False, include_sensitive=False):
        """Convert conversation to dictionary"""
        conv_dict = {
            'id': self.id,
            'session_id': self.session_id,
            'message': self.message if include_sensitive else self.message[:100] + "..." if len(self.message) > 100 else self.message,
            'response': self.response,
            'sentiment': self.sentiment,
            'topic': self.topic,
            'language_detected': self.language_detected,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'conversation_completed': self.conversation_completed
        }
        
        if include_analysis:
            conv_dict.update({
                'sentiment_score': self.sentiment_score,
                'emotion_analysis': self.emotion_analysis,
                'risk_level': self.risk_level,
                'therapeutic_technique': self.therapeutic_technique,
                'coping_strategies_suggested': self.coping_strategies_suggested,
                'user_receptiveness': self.user_receptiveness,
                'conversation_value': self.calculate_conversation_value(),
                'insights': self.get_conversation_insights()
            })
        
        if include_sensitive:
            conv_dict.update({
                'crisis_indicators': self.crisis_indicators,
                'intervention_triggered': self.intervention_triggered,
                'flagged_for_review': self.flagged_for_review
            })
        
        return conv_dict
    
    @classmethod
    def get_conversation_analytics(cls, user_id, days=30):
        """Get conversation analytics for user"""
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conversations = cls.query.filter(
            cls.user_id == user_id,
            cls.timestamp >= start_date
        ).all()
        
        if not conversations:
            return None
        
        # Calculate analytics
        total_conversations = len(conversations)
        avg_sentiment = sum(c.sentiment_score or 0 for c in conversations) / total_conversations
        
        # Topic analysis
        topic_count = {}
        for conv in conversations:
            if conv.topic:
                topic_count[conv.topic] = topic_count.get(conv.topic, 0) + 1
        
        most_discussed_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Risk analysis
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for conv in conversations:
            risk_distribution[conv.risk_level] = risk_distribution.get(conv.risk_level, 0) + 1
        
        # Therapeutic techniques used
        technique_count = {}
        for conv in conversations:
            if conv.therapeutic_technique:
                technique_count[conv.therapeutic_technique] = technique_count.get(conv.therapeutic_technique, 0) + 1
        
        # User engagement
        total_satisfaction = sum(c.user_satisfaction for c in conversations if c.user_satisfaction)
        satisfaction_count = len([c for c in conversations if c.user_satisfaction])
        avg_satisfaction = total_satisfaction / satisfaction_count if satisfaction_count > 0 else None
        
        return {
            'total_conversations': total_conversations,
            'average_sentiment': avg_sentiment,
            'most_discussed_topics': most_discussed_topics,
            'risk_distribution': risk_distribution,
            'therapeutic_techniques_used': technique_count,
            'average_satisfaction': avg_satisfaction,
            'interventions_triggered': len([c for c in conversations if c.intervention_triggered]),
            'total_conversation_value': sum(c.calculate_conversation_value() for c in conversations)
        }
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.topic or "General"} - {self.sentiment}>'