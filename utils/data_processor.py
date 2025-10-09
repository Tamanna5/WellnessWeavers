"""
Data Processing Utilities for WellnessWeavers
Data analysis, insights generation, and pattern recognition
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Utility class for processing and analyzing user data"""
    
    def __init__(self):
        self.insight_thresholds = {
            'mood_volatility': 2.0,  # Standard deviation threshold
            'low_mood_frequency': 0.3,  # 30% of entries below 4
            'high_mood_frequency': 0.7,  # 70% of entries above 7
            'consistency_threshold': 0.8  # 80% tracking consistency
        }
    
    def analyze_mood_patterns(self, mood_data: List[Dict]) -> Dict:
        """Analyze mood patterns and generate insights"""
        if not mood_data:
            return {'error': 'No mood data available'}
        
        # Extract mood scores and timestamps
        scores = [entry['mood_score'] for entry in mood_data]
        timestamps = [entry['created_at'] for entry in mood_data]
        
        # Basic statistics
        avg_mood = statistics.mean(scores)
        mood_std = statistics.stdev(scores) if len(scores) > 1 else 0
        min_mood = min(scores)
        max_mood = max(scores)
        
        # Trend analysis
        trend = self._calculate_trend(scores)
        
        # Volatility analysis
        volatility = self._calculate_volatility(scores)
        
        # Day of week patterns
        day_patterns = self._analyze_day_patterns(mood_data)
        
        # Time of day patterns
        time_patterns = self._analyze_time_patterns(mood_data)
        
        # Mood distribution
        mood_distribution = self._analyze_mood_distribution(scores)
        
        return {
            'average_mood': round(avg_mood, 2),
            'mood_std': round(mood_std, 2),
            'min_mood': min_mood,
            'max_mood': max_mood,
            'trend': trend,
            'volatility': volatility,
            'day_patterns': day_patterns,
            'time_patterns': time_patterns,
            'mood_distribution': mood_distribution,
            'total_entries': len(scores),
            'date_range': {
                'start': min(timestamps),
                'end': max(timestamps)
            }
        }
    
    def generate_wellness_insights(self, user_data: Dict) -> List[Dict]:
        """Generate personalized wellness insights"""
        insights = []
        
        # Mood trend insights
        if 'mood_trend' in user_data:
            if user_data['mood_trend'] == 'declining':
                insights.append({
                    'type': 'concern',
                    'title': 'Declining Mood Trend',
                    'message': 'Your mood has been declining recently. Consider reaching out for support.',
                    'action': 'Schedule a therapy session',
                    'priority': 'high',
                    'confidence': 0.8
                })
            elif user_data['mood_trend'] == 'improving':
                insights.append({
                    'type': 'positive',
                    'title': 'Improving Mood Trend',
                    'message': 'Great news! Your mood has been improving. Keep up the good work!',
                    'action': 'Continue current activities',
                    'priority': 'low',
                    'confidence': 0.9
                })
        
        # Volatility insights
        if 'mood_volatility' in user_data:
            if user_data['mood_volatility'] > self.insight_thresholds['mood_volatility']:
                insights.append({
                    'type': 'info',
                    'title': 'High Mood Volatility',
                    'message': 'Your mood has been quite variable recently. This might indicate stress or emotional instability.',
                    'action': 'Try stress management techniques',
                    'priority': 'medium',
                    'confidence': 0.7
                })
        
        # Consistency insights
        if 'tracking_consistency' in user_data:
            if user_data['tracking_consistency'] < self.insight_thresholds['consistency_threshold']:
                insights.append({
                    'type': 'reminder',
                    'title': 'Tracking Consistency',
                    'message': 'Regular mood tracking helps identify patterns and triggers.',
                    'action': 'Set daily reminders',
                    'priority': 'medium',
                    'confidence': 0.6
                })
        
        # Day pattern insights
        if 'day_patterns' in user_data:
            worst_day = min(user_data['day_patterns'].items(), key=lambda x: x[1])
            if worst_day[1] < 5:
                insights.append({
                    'type': 'info',
                    'title': f'Challenging {worst_day[0]}s',
                    'message': f'You tend to feel lower on {worst_day[0]}s. Consider planning enjoyable activities.',
                    'action': 'Plan self-care activities',
                    'priority': 'medium',
                    'confidence': 0.7
                })
        
        return insights
    
    def calculate_wellness_score(self, user_data: Dict) -> float:
        """Calculate comprehensive wellness score"""
        score = 50.0  # Base score
        
        # Mood factor (40% weight)
        if 'average_mood' in user_data:
            mood_score = (user_data['average_mood'] / 10) * 100
            score += (mood_score - 50) * 0.4
        
        # Consistency factor (20% weight)
        if 'tracking_consistency' in user_data:
            consistency_bonus = (user_data['tracking_consistency'] - 0.5) * 20
            score += consistency_bonus * 0.2
        
        # Streak factor (15% weight)
        if 'streak_days' in user_data:
            streak_bonus = min(user_data['streak_days'] * 2, 20)
            score += streak_bonus * 0.15
        
        # Activity factor (15% weight)
        if 'activity_level' in user_data:
            activity_bonus = (user_data['activity_level'] - 5) * 4
            score += activity_bonus * 0.15
        
        # Social factor (10% weight)
        if 'social_interactions' in user_data:
            social_bonus = min(user_data['social_interactions'] * 5, 20)
            score += social_bonus * 0.1
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def predict_mood_trends(self, mood_data: List[Dict], days_ahead: int = 7) -> Dict:
        """Predict future mood trends"""
        if len(mood_data) < 7:
            return {'error': 'Insufficient data for prediction'}
        
        # Extract recent mood scores
        recent_scores = [entry['mood_score'] for entry in mood_data[-14:]]  # Last 2 weeks
        
        # Simple linear regression for trend
        trend_slope = self._calculate_trend_slope(recent_scores)
        
        # Predict future scores
        predictions = []
        current_score = recent_scores[-1]
        
        for day in range(1, days_ahead + 1):
            predicted_score = current_score + (trend_slope * day)
            # Add some randomness to simulate real-world variation
            import random
            variation = random.uniform(-0.5, 0.5)
            predicted_score = max(1, min(10, predicted_score + variation))
            predictions.append({
                'day': day,
                'predicted_score': round(predicted_score, 2),
                'confidence': max(0.3, 1.0 - (day * 0.1))  # Decreasing confidence
            })
        
        return {
            'predictions': predictions,
            'trend_direction': 'improving' if trend_slope > 0 else 'declining' if trend_slope < 0 else 'stable',
            'confidence': 0.7
        }
    
    def identify_triggers(self, mood_data: List[Dict], activity_data: List[Dict] = None) -> List[Dict]:
        """Identify potential mood triggers"""
        triggers = []
        
        # Analyze mood patterns
        low_mood_entries = [entry for entry in mood_data if entry['mood_score'] <= 3]
        high_mood_entries = [entry for entry in mood_data if entry['mood_score'] >= 8]
        
        # Day of week analysis
        day_patterns = {}
        for entry in mood_data:
            day = entry['created_at'].strftime('%A')
            if day not in day_patterns:
                day_patterns[day] = []
            day_patterns[day].append(entry['mood_score'])
        
        for day, scores in day_patterns.items():
            avg_score = statistics.mean(scores)
            if avg_score <= 4:
                triggers.append({
                    'type': 'day_of_week',
                    'trigger': day,
                    'impact': 'negative',
                    'confidence': 0.7,
                    'description': f'You tend to feel lower on {day}s'
                })
            elif avg_score >= 8:
                triggers.append({
                    'type': 'day_of_week',
                    'trigger': day,
                    'impact': 'positive',
                    'confidence': 0.7,
                    'description': f'You tend to feel better on {day}s'
                })
        
        # Time of day analysis
        time_patterns = {}
        for entry in mood_data:
            hour = entry['created_at'].hour
            time_period = 'morning' if hour < 12 else 'afternoon' if hour < 18 else 'evening'
            if time_period not in time_patterns:
                time_patterns[time_period] = []
            time_patterns[time_period].append(entry['mood_score'])
        
        for period, scores in time_patterns.items():
            if len(scores) >= 3:  # Minimum data points
                avg_score = statistics.mean(scores)
                if avg_score <= 4:
                    triggers.append({
                        'type': 'time_of_day',
                        'trigger': period,
                        'impact': 'negative',
                        'confidence': 0.6,
                        'description': f'You tend to feel lower in the {period}'
                    })
        
        # Activity correlation (if available)
        if activity_data:
            activity_correlations = self._analyze_activity_correlations(mood_data, activity_data)
            triggers.extend(activity_correlations)
        
        return triggers
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate mood trend direction"""
        if len(scores) < 3:
            return 'insufficient_data'
        
        # Simple trend calculation
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        difference = second_avg - first_avg
        
        if difference > 0.5:
            return 'improving'
        elif difference < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate mood volatility (standard deviation)"""
        if len(scores) < 2:
            return 0.0
        return statistics.stdev(scores)
    
    def _analyze_day_patterns(self, mood_data: List[Dict]) -> Dict:
        """Analyze mood patterns by day of week"""
        day_scores = {}
        
        for entry in mood_data:
            day = entry['created_at'].strftime('%A')
            if day not in day_scores:
                day_scores[day] = []
            day_scores[day].append(entry['mood_score'])
        
        day_averages = {}
        for day, scores in day_scores.items():
            if scores:
                day_averages[day] = round(statistics.mean(scores), 2)
        
        return day_averages
    
    def _analyze_time_patterns(self, mood_data: List[Dict]) -> Dict:
        """Analyze mood patterns by time of day"""
        time_scores = {}
        
        for entry in mood_data:
            hour = entry['created_at'].hour
            time_period = 'morning' if hour < 12 else 'afternoon' if hour < 18 else 'evening'
            if time_period not in time_scores:
                time_scores[time_period] = []
            time_scores[time_period].append(entry['mood_score'])
        
        time_averages = {}
        for period, scores in time_scores.items():
            if scores:
                time_averages[period] = round(statistics.mean(scores), 2)
        
        return time_averages
    
    def _analyze_mood_distribution(self, scores: List[float]) -> Dict:
        """Analyze distribution of mood scores"""
        distribution = {
            'very_low': len([s for s in scores if s <= 2]),
            'low': len([s for s in scores if 3 <= s <= 4]),
            'neutral': len([s for s in scores if 5 <= s <= 6]),
            'good': len([s for s in scores if 7 <= s <= 8]),
            'excellent': len([s for s in scores if s >= 9])
        }
        
        # Convert to percentages
        total = len(scores)
        if total > 0:
            for key in distribution:
                distribution[key] = round((distribution[key] / total) * 100, 1)
        
        return distribution
    
    def _calculate_trend_slope(self, scores: List[float]) -> float:
        """Calculate slope of mood trend"""
        if len(scores) < 2:
            return 0.0
        
        n = len(scores)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _analyze_activity_correlations(self, mood_data: List[Dict], activity_data: List[Dict]) -> List[Dict]:
        """Analyze correlations between activities and mood"""
        correlations = []
        
        # This is a simplified correlation analysis
        # In a real implementation, you'd use proper statistical methods
        
        activity_mood_map = {}
        for mood_entry in mood_data:
            date = mood_entry['created_at'].date()
            for activity_entry in activity_data:
                if activity_entry['date'] == date:
                    activity = activity_entry['activity']
                    if activity not in activity_mood_map:
                        activity_mood_map[activity] = []
                    activity_mood_map[activity].append(mood_entry['mood_score'])
        
        for activity, scores in activity_mood_map.items():
            if len(scores) >= 3:  # Minimum data points
                avg_mood = statistics.mean(scores)
                if avg_mood >= 7:
                    correlations.append({
                        'type': 'activity',
                        'trigger': activity,
                        'impact': 'positive',
                        'confidence': 0.6,
                        'description': f'{activity} tends to improve your mood'
                    })
                elif avg_mood <= 4:
                    correlations.append({
                        'type': 'activity',
                        'trigger': activity,
                        'impact': 'negative',
                        'confidence': 0.6,
                        'description': f'{activity} tends to lower your mood'
                    })
        
        return correlations

# Global instance
data_processor = DataProcessor()
