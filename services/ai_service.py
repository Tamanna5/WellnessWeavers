"""
AI Service for WellnessWeavers
Google Cloud AI integration for mental health support
"""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered mental health support"""
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_CLOUD_API_KEY')
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
        self.base_url = "https://language.googleapis.com/v1"
        
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using Google Cloud Natural Language API"""
        if not self.api_key:
            return self._fallback_sentiment_analysis(text)
        
        try:
            url = f"{self.base_url}/documents:analyzeSentiment"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "document": {
                    "type": "PLAIN_TEXT",
                    "content": text
                },
                "encodingType": "UTF8"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'sentiment_score': result['documentSentiment']['score'],
                'sentiment_magnitude': result['documentSentiment']['magnitude'],
                'sentiment_label': self._get_sentiment_label(result['documentSentiment']['score']),
                'confidence': result['documentSentiment']['magnitude']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return self._fallback_sentiment_analysis(text)
    
    def detect_emotions(self, text: str) -> List[Dict]:
        """Detect emotions in text"""
        emotions = []
        
        # Emotion keywords mapping
        emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'cheerful', 'delighted', 'pleased', 'content'],
            'sad': ['sad', 'depressed', 'down', 'blue', 'melancholy', 'gloomy', 'unhappy'],
            'angry': ['angry', 'mad', 'furious', 'irritated', 'annoyed', 'rage', 'frustrated'],
            'anxious': ['anxious', 'worried', 'nervous', 'anxious', 'stressed', 'tense', 'uneasy'],
            'fearful': ['afraid', 'scared', 'terrified', 'fearful', 'panic', 'dread', 'alarmed'],
            'surprised': ['surprised', 'shocked', 'amazed', 'astonished', 'startled', 'bewildered'],
            'disgusted': ['disgusted', 'repulsed', 'revolted', 'sickened', 'appalled', 'horrified']
        }
        
        text_lower = text.lower()
        
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                emotions.append({
                    'emotion': emotion,
                    'intensity': min(count / len(keywords), 1.0),
                    'confidence': min(count * 0.3, 0.9)
                })
        
        return emotions
    
    def generate_response(self, user_message: str, context: Dict = None) -> str:
        """Generate AI response based on user message and context"""
        # Analyze user message
        sentiment = self.analyze_sentiment(user_message)
        emotions = self.detect_emotions(user_message)
        
        # Determine response strategy
        if sentiment['sentiment_score'] < -0.5:
            return self._generate_supportive_response(user_message, emotions)
        elif sentiment['sentiment_score'] > 0.5:
            return self._generate_encouraging_response(user_message, emotions)
        else:
            return self._generate_neutral_response(user_message, emotions)
    
    def _generate_supportive_response(self, message: str, emotions: List[Dict]) -> str:
        """Generate supportive response for negative sentiment"""
        responses = [
            "I can hear that you're going through a difficult time. It's okay to feel this way, and I'm here to listen and support you.",
            "I understand that things feel overwhelming right now. Remember that these feelings are temporary, and you're stronger than you think.",
            "It sounds like you're carrying a heavy emotional load. Would you like to talk about what's been weighing on you?",
            "I can sense the pain in your words. You don't have to face this alone - I'm here to help you through this.",
            "Your feelings are completely valid. Sometimes just acknowledging them is the first step toward healing."
        ]
        
        # Add emotion-specific responses
        if any(e['emotion'] in ['sad', 'depressed'] for e in emotions):
            responses.extend([
                "I can feel the sadness in your message. It's important to remember that depression is treatable, and you don't have to suffer alone.",
                "The weight of sadness can feel crushing. Have you considered reaching out to a mental health professional? They can provide the support you need."
            ])
        
        if any(e['emotion'] in ['anxious', 'worried'] for e in emotions):
            responses.extend([
                "I can sense the anxiety in your words. Let's try some breathing exercises together. Inhale for 4 counts, hold for 4, exhale for 4.",
                "Anxiety can make everything feel overwhelming. Remember to take things one step at a time, and don't hesitate to seek professional help."
            ])
        
        return responses[0]  # Return first response for now
    
    def _generate_encouraging_response(self, message: str, emotions: List[Dict]) -> str:
        """Generate encouraging response for positive sentiment"""
        responses = [
            "I'm so glad to hear that you're feeling positive! It's wonderful to see you in good spirits.",
            "Your positive energy is contagious! Keep up the great work and continue taking care of yourself.",
            "It's fantastic to hear about your progress! Remember to celebrate these moments of joy.",
            "Your optimism is inspiring! Continue nurturing this positive mindset.",
            "I love hearing about your successes! You're doing an amazing job on your wellness journey."
        ]
        
        return responses[0]
    
    def _generate_neutral_response(self, message: str, emotions: List[Dict]) -> str:
        """Generate neutral response for neutral sentiment"""
        responses = [
            "Thank you for sharing that with me. I'm here to listen and support you in whatever way you need.",
            "I appreciate you opening up to me. How can I best support you today?",
            "It sounds like you're processing a lot right now. I'm here to help you work through whatever you're experiencing.",
            "Thank you for trusting me with your thoughts. What would be most helpful for you right now?",
            "I'm listening and here to support you. What's on your mind today?"
        ]
        
        return responses[0]
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.5:
            return 'positive'
        elif score <= -0.5:
            return 'negative'
        else:
            return 'neutral'
    
    def _fallback_sentiment_analysis(self, text: str) -> Dict:
        """Fallback sentiment analysis when API is not available"""
        positive_words = ['good', 'great', 'excellent', 'happy', 'joy', 'love', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'sad', 'angry', 'hate', 'horrible', 'depressed', 'anxious']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            score = 0.3
        elif negative_count > positive_count:
            score = -0.3
        else:
            score = 0.0
        
        return {
            'sentiment_score': score,
            'sentiment_magnitude': abs(score),
            'sentiment_label': self._get_sentiment_label(score),
            'confidence': 0.5
        }
    
    def generate_wellness_insights(self, user_data: Dict) -> List[Dict]:
        """Generate personalized wellness insights based on user data"""
        insights = []
        
        # Mood trend analysis
        if 'mood_trend' in user_data:
            if user_data['mood_trend'] == 'declining':
                insights.append({
                    'type': 'concern',
                    'title': 'Declining Mood Trend',
                    'message': 'Your mood has been declining recently. Consider reaching out for support.',
                    'action': 'Schedule a therapy session',
                    'priority': 'high'
                })
            elif user_data['mood_trend'] == 'improving':
                insights.append({
                    'type': 'positive',
                    'title': 'Improving Mood Trend',
                    'message': 'Great news! Your mood has been improving. Keep up the good work!',
                    'action': 'Continue current activities',
                    'priority': 'low'
                })
        
        # Streak analysis
        if 'streak_days' in user_data:
            if user_data['streak_days'] >= 7:
                insights.append({
                    'type': 'achievement',
                    'title': f'{user_data["streak_days"]} Day Streak!',
                    'message': 'Consistency is key to mental wellness. You\'re doing great!',
                    'priority': 'medium'
                })
            elif user_data['streak_days'] == 0:
                insights.append({
                    'type': 'reminder',
                    'title': 'Mood Check Reminder',
                    'message': 'Regular check-ins help track your progress.',
                    'action': 'Log today\'s mood',
                    'priority': 'medium'
                })
        
        # Wellness score analysis
        if 'wellness_score' in user_data:
            score = user_data['wellness_score']
            if score < 40:
                insights.append({
                    'type': 'concern',
                    'title': 'Wellness Score Needs Attention',
                    'message': 'Your wellness score has been low. Consider reaching out to a professional.',
                    'action': 'Book a therapy session',
                    'priority': 'high'
                })
            elif score > 80:
                insights.append({
                    'type': 'positive',
                    'title': 'Excellent Wellness Score!',
                    'message': 'Your wellness score is excellent. Keep up the great work!',
                    'priority': 'low'
                })
        
        return insights
    
    def suggest_coping_strategies(self, emotions: List[Dict], context: Dict = None) -> List[str]:
        """Suggest coping strategies based on detected emotions"""
        strategies = []
        
        for emotion in emotions:
            if emotion['emotion'] == 'anxious':
                strategies.extend([
                    "Try deep breathing exercises: 4-7-8 breathing technique",
                    "Practice progressive muscle relaxation",
                    "Use grounding techniques: 5-4-3-2-1 method",
                    "Consider mindfulness meditation"
                ])
            elif emotion['emotion'] == 'sad':
                strategies.extend([
                    "Engage in gentle physical activity like walking",
                    "Connect with a trusted friend or family member",
                    "Practice self-compassion and self-care",
                    "Consider journaling your feelings"
                ])
            elif emotion['emotion'] == 'angry':
                strategies.extend([
                    "Take a break and step away from the situation",
                    "Practice counting to 10 before responding",
                    "Use physical exercise to release tension",
                    "Try journaling to express your feelings"
                ])
        
        return strategies[:3]  # Return top 3 strategies

# Global instance
ai_service = AIService()
