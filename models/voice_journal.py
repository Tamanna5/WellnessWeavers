"""
Voice Journal Model for WellnessWeavers
Voice-based mood tracking with comprehensive audio analysis
"""

from database import db
from datetime import datetime
import json
import os

class VoiceJournal(db.Model):
    """Voice journal entries with audio analysis"""
    __tablename__ = 'voice_journals'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Audio file information
    audio_file_path = db.Column(db.String(500))  # Path to stored audio file
    audio_file_size = db.Column(db.Integer)  # File size in bytes
    audio_format = db.Column(db.String(10), default='wav')  # wav, mp3, m4a
    duration_seconds = db.Column(db.Float)  # Duration in seconds
    
    # Transcription
    transcription = db.Column(db.Text)  # Speech-to-text result
    transcription_confidence = db.Column(db.Float)  # Confidence score 0-1
    language_detected = db.Column(db.String(10))  # Detected language code
    contains_code_switching = db.Column(db.Boolean, default=False)  # Multiple languages
    
    # Voice analysis features
    average_pitch_hz = db.Column(db.Float)  # Average fundamental frequency
    pitch_variance = db.Column(db.Float)  # Pitch variation
    speech_rate_wpm = db.Column(db.Integer)  # Words per minute
    volume_db = db.Column(db.Float)  # Average volume level
    vocal_energy = db.Column(db.Float)  # Voice energy level
    
    # Emotional indicators from voice
    voice_emotion_detected = db.Column(db.JSON)  # Emotions detected from voice
    stress_level = db.Column(db.Float)  # 0-1 scale from voice patterns
    anxiety_indicators = db.Column(db.JSON)  # Specific anxiety markers
    depression_indicators = db.Column(db.JSON)  # Speech patterns indicating depression
    
    # Special detection
    crying_detected = db.Column(db.Boolean, default=False)
    laughter_detected = db.Column(db.Boolean, default=False)
    breathing_irregularities = db.Column(db.Boolean, default=False)
    voice_tremor_detected = db.Column(db.Boolean, default=False)
    
    # Content analysis (from transcription)
    sentiment_score = db.Column(db.Float)  # -1 to 1 sentiment
    topic_tags = db.Column(db.JSON)  # Topics mentioned
    trigger_words_detected = db.Column(db.JSON)  # Mental health triggers
    coping_mechanisms_mentioned = db.Column(db.JSON)  # User mentioned coping
    
    # Risk assessment
    crisis_indicators = db.Column(db.JSON)  # Crisis language detected
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    professional_review_flagged = db.Column(db.Boolean, default=False)
    
    # User context at time of recording
    location_context = db.Column(db.String(100))  # Where recorded
    mood_before = db.Column(db.Integer)  # Mood before recording (1-10)
    mood_after = db.Column(db.Integer)  # Mood after recording (1-10)
    activity_before = db.Column(db.String(100))  # What user was doing
    
    # Processing metadata
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    processing_started_at = db.Column(db.DateTime)
    processing_completed_at = db.Column(db.DateTime)
    processing_errors = db.Column(db.JSON)  # Any errors during processing
    
    # Privacy and sharing
    is_private = db.Column(db.Boolean, default=True)
    shared_with_therapist = db.Column(db.Boolean, default=False)
    anonymous_research_consent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='voice_journals')
    
    def analyze_audio_file(self, ai_service):
        """Comprehensive audio analysis using AI services"""
        if not self.audio_file_path or not os.path.exists(self.audio_file_path):
            return False
        
        self.processing_status = 'processing'
        self.processing_started_at = datetime.utcnow()
        
        try:
            # Speech-to-text transcription
            transcription_result = ai_service.transcribe_audio(self.audio_file_path)
            self.transcription = transcription_result.get('transcript', '')
            self.transcription_confidence = transcription_result.get('confidence', 0.0)
            self.language_detected = transcription_result.get('language', 'en')
            
            # Audio feature extraction
            audio_features = ai_service.extract_audio_features(self.audio_file_path)
            self.duration_seconds = audio_features.get('duration', 0.0)
            self.average_pitch_hz = audio_features.get('pitch_mean', 0.0)
            self.pitch_variance = audio_features.get('pitch_variance', 0.0)
            self.speech_rate_wpm = audio_features.get('speech_rate', 0)
            self.volume_db = audio_features.get('volume_mean', 0.0)
            self.vocal_energy = audio_features.get('vocal_energy', 0.0)
            
            # Emotional analysis from voice
            emotion_analysis = ai_service.analyze_voice_emotions(self.audio_file_path)
            self.voice_emotion_detected = emotion_analysis.get('emotions', [])
            self.stress_level = emotion_analysis.get('stress_level', 0.0)
            self.anxiety_indicators = emotion_analysis.get('anxiety_markers', [])
            self.depression_indicators = emotion_analysis.get('depression_markers', [])
            
            # Special audio events detection
            audio_events = ai_service.detect_audio_events(self.audio_file_path)
            self.crying_detected = audio_events.get('crying', False)
            self.laughter_detected = audio_events.get('laughter', False)
            self.breathing_irregularities = audio_events.get('irregular_breathing', False)
            self.voice_tremor_detected = audio_events.get('voice_tremor', False)
            
            # Content analysis from transcription
            if self.transcription:
                content_analysis = ai_service.analyze_text_content(self.transcription)
                self.sentiment_score = content_analysis.get('sentiment_score', 0.0)
                self.topic_tags = content_analysis.get('topics', [])
                self.trigger_words_detected = content_analysis.get('triggers', [])
                self.coping_mechanisms_mentioned = content_analysis.get('coping_mechanisms', [])
                
                # Crisis detection
                crisis_analysis = ai_service.detect_crisis_language(self.transcription)
                self.crisis_indicators = crisis_analysis.get('indicators', [])
                self.risk_level = crisis_analysis.get('risk_level', 'low')
                
                if self.risk_level in ['high', 'critical']:
                    self.professional_review_flagged = True
                    self._create_crisis_alert()
            
            # Code-switching detection
            self.contains_code_switching = ai_service.detect_code_switching(self.transcription)
            
            self.processing_status = 'completed'
            self.processing_completed_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            self.processing_status = 'failed'
            self.processing_errors = {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
            print(f"Voice journal analysis failed for {self.id}: {str(e)}")
            return False
    
    def _create_crisis_alert(self):
        """Create crisis alert if high-risk content detected"""
        from models.crisis import CrisisAlert
        
        alert = CrisisAlert(
            user_id=self.user_id,
            severity=self.risk_level,
            trigger_source='voice_journal',
            context=self.transcription[:500] if self.transcription else 'Voice analysis detected crisis indicators',
            indicators=self.crisis_indicators
        )
        db.session.add(alert)
    
    def calculate_wellness_impact(self):
        """Calculate impact on user's wellness score"""
        impact = 0
        
        # Positive impact for using the tool
        impact += 2  # Base points for self-expression
        
        # Duration bonus (longer entries show more engagement)
        if self.duration_seconds:
            if self.duration_seconds > 60:  # Over 1 minute
                impact += 3
            if self.duration_seconds > 180:  # Over 3 minutes
                impact += 2
        
        # Sentiment impact
        if self.sentiment_score:
            if self.sentiment_score > 0.3:
                impact += 3  # Positive content
            elif self.sentiment_score < -0.3:
                impact -= 2  # Negative content (still processing emotions)
        
        # Coping mechanisms mentioned
        if self.coping_mechanisms_mentioned:
            impact += len(self.coping_mechanisms_mentioned) * 2
        
        # Risk penalty
        risk_penalties = {'low': 0, 'medium': -1, 'high': -3, 'critical': -5}
        impact += risk_penalties.get(self.risk_level, 0)
        
        # Special events
        if self.crying_detected:
            impact += 1  # Emotional release can be therapeutic
        if self.laughter_detected:
            impact += 3  # Laughter is beneficial
        
        return max(-5, min(10, impact))  # Clamp between -5 and 10
    
    def get_voice_insights(self):
        """Generate insights from voice analysis"""
        insights = []
        
        # Vocal stress indicators
        if self.stress_level and self.stress_level > 0.7:
            insights.append({
                'type': 'concern',
                'category': 'stress',
                'title': 'High Vocal Stress Detected',
                'message': 'Your voice patterns suggest high stress levels.',
                'recommendation': 'Consider some relaxation techniques or breathing exercises.'
            })
        
        # Speech patterns
        if self.speech_rate_wpm:
            if self.speech_rate_wpm > 180:
                insights.append({
                    'type': 'pattern',
                    'category': 'speech',
                    'title': 'Rapid Speech Detected',
                    'message': 'You\'re speaking quite quickly, which can indicate anxiety or excitement.',
                    'recommendation': 'Try slowing down your speech with deep breathing.'
                })
            elif self.speech_rate_wpm < 100:
                insights.append({
                    'type': 'pattern',
                    'category': 'speech',
                    'title': 'Slow Speech Pattern',
                    'message': 'Your speech is slower than usual, which might indicate low energy or sadness.',
                    'recommendation': 'Consider activities that boost your energy.'
                })
        
        # Emotional indicators
        if self.voice_emotion_detected:
            primary_emotion = max(self.voice_emotion_detected, key=lambda x: x.get('confidence', 0))
            insights.append({
                'type': 'emotion',
                'category': 'voice_emotion',
                'title': f'Primary Emotion: {primary_emotion.get("emotion", "Unknown").title()}',
                'message': f'Your voice primarily conveys {primary_emotion.get("emotion", "unknown")} emotion.',
                'confidence': primary_emotion.get('confidence', 0)
            })
        
        # Content insights
        if self.topic_tags:
            most_discussed = self.topic_tags[:3]  # Top 3 topics
            insights.append({
                'type': 'content',
                'category': 'topics',
                'title': 'Main Topics Discussed',
                'message': f'You mainly talked about: {", ".join(most_discussed)}',
                'topics': most_discussed
            })
        
        # Positive indicators
        if self.laughter_detected:
            insights.append({
                'type': 'positive',
                'category': 'mood',
                'title': 'Laughter Detected!',
                'message': 'It\'s great to hear you laughing - that\'s a wonderful sign!',
                'recommendation': 'Keep finding things that bring you joy.'
            })
        
        # Coping mechanisms
        if self.coping_mechanisms_mentioned:
            insights.append({
                'type': 'positive',
                'category': 'coping',
                'title': 'Coping Strategies Mentioned',
                'message': f'You mentioned these coping strategies: {", ".join(self.coping_mechanisms_mentioned[:3])}',
                'recommendation': 'It\'s excellent that you\'re actively using coping strategies.'
            })
        
        return insights
    
    def get_transcription_summary(self, max_length=200):
        """Get a summary of the transcription"""
        if not self.transcription:
            return "No transcription available."
        
        if len(self.transcription) <= max_length:
            return self.transcription
        
        # Simple truncation with ellipsis
        return self.transcription[:max_length-3] + "..."
    
    def to_dict(self, include_analysis=False, include_audio_path=False):
        """Convert to dictionary representation"""
        voice_dict = {
            'id': self.id,
            'duration_seconds': self.duration_seconds,
            'transcription_summary': self.get_transcription_summary(),
            'language_detected': self.language_detected,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'processing_status': self.processing_status,
            'wellness_impact': self.calculate_wellness_impact()
        }
        
        if include_analysis:
            voice_dict.update({
                'transcription': self.transcription,
                'transcription_confidence': self.transcription_confidence,
                'voice_emotion_detected': self.voice_emotion_detected,
                'sentiment_score': self.sentiment_score,
                'stress_level': self.stress_level,
                'topic_tags': self.topic_tags,
                'risk_level': self.risk_level,
                'insights': self.get_voice_insights(),
                'audio_features': {
                    'pitch': self.average_pitch_hz,
                    'speech_rate': self.speech_rate_wpm,
                    'vocal_energy': self.vocal_energy,
                    'volume': self.volume_db
                },
                'special_events': {
                    'crying_detected': self.crying_detected,
                    'laughter_detected': self.laughter_detected,
                    'breathing_irregularities': self.breathing_irregularities
                }
            })
        
        if include_audio_path:
            voice_dict['audio_file_path'] = self.audio_file_path
        
        return voice_dict
    
    @classmethod
    def get_voice_analytics(cls, user_id, days=30):
        """Get voice journal analytics for user"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        entries = cls.query.filter(
            cls.user_id == user_id,
            cls.recorded_at >= start_date,
            cls.processing_status == 'completed'
        ).all()
        
        if not entries:
            return None
        
        # Calculate analytics
        total_entries = len(entries)
        total_duration = sum(e.duration_seconds or 0 for e in entries)
        avg_duration = total_duration / total_entries if total_entries > 0 else 0
        
        # Sentiment trend
        sentiment_scores = [e.sentiment_score for e in entries if e.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Stress level trend
        stress_levels = [e.stress_level for e in entries if e.stress_level is not None]
        avg_stress = sum(stress_levels) / len(stress_levels) if stress_levels else 0
        
        # Topic analysis
        all_topics = []
        for entry in entries:
            if entry.topic_tags:
                all_topics.extend(entry.topic_tags)
        
        topic_frequency = {}
        for topic in all_topics:
            topic_frequency[topic] = topic_frequency.get(topic, 0) + 1
        
        most_discussed_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Special events frequency
        crying_count = sum(1 for e in entries if e.crying_detected)
        laughter_count = sum(1 for e in entries if e.laughter_detected)
        
        return {
            'total_entries': total_entries,
            'total_duration_minutes': round(total_duration / 60, 1),
            'average_duration_minutes': round(avg_duration / 60, 1),
            'average_sentiment': round(avg_sentiment, 2),
            'average_stress_level': round(avg_stress, 2),
            'most_discussed_topics': most_discussed_topics,
            'emotional_events': {
                'crying_episodes': crying_count,
                'laughter_episodes': laughter_count
            },
            'engagement_trend': cls._calculate_engagement_trend(entries)
        }
    
    @staticmethod
    def _calculate_engagement_trend(entries):
        """Calculate if user is becoming more or less engaged"""
        if len(entries) < 5:
            return 'insufficient_data'
        
        # Compare recent entries with earlier ones
        recent_avg_duration = sum(e.duration_seconds or 0 for e in entries[-5:]) / 5
        earlier_avg_duration = sum(e.duration_seconds or 0 for e in entries[:5]) / 5
        
        if recent_avg_duration > earlier_avg_duration * 1.2:
            return 'increasing'
        elif recent_avg_duration < earlier_avg_duration * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def delete_audio_file(self):
        """Safely delete the audio file from storage"""
        if self.audio_file_path and os.path.exists(self.audio_file_path):
            try:
                os.remove(self.audio_file_path)
                self.audio_file_path = None
                return True
            except Exception as e:
                print(f"Error deleting audio file {self.audio_file_path}: {str(e)}")
                return False
        return False
    
    def __repr__(self):
        duration = f"{self.duration_seconds:.1f}s" if self.duration_seconds else "Unknown"
        return f'<VoiceJournal {self.id}: {duration} - {self.processing_status}>'