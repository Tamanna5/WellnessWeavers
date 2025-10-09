"""
Seasonal Pattern Tracking Service for WellnessWeavers
Detect Seasonal Affective Disorder (SAD) patterns and provide interventions
"""

import statistics
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeasonalTracker:
    """Service for tracking seasonal mood patterns and SAD detection"""
    
    def __init__(self):
        self.seasonal_months = {
            'winter': [12, 1, 2],  # December, January, February
            'spring': [3, 4, 5],    # March, April, May
            'summer': [6, 7, 8],    # June, July, August
            'autumn': [9, 10, 11]   # September, October, November
        }
        
        self.sad_symptoms = [
            'low_energy',
            'increased_sleep',
            'weight_gain',
            'carbohydrate_craving',
            'social_withdrawal',
            'difficulty_concentrating',
            'hopelessness',
            'irritability'
        ]
    
    def analyze_seasonal_patterns(self, mood_data: List[Dict], days: int = 365) -> Dict:
        """Analyze mood data for seasonal patterns"""
        if not mood_data or len(mood_data) < 30:
            return {'error': 'Insufficient data for seasonal analysis'}
        
        # Filter data to specified time period
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_data = [entry for entry in mood_data 
                      if entry['created_at'] >= cutoff_date]
        
        if not recent_data:
            return {'error': 'No recent data available'}
        
        # Group by month
        monthly_moods = {}
        for entry in recent_data:
            month = entry['created_at'].month
            if month not in monthly_moods:
                monthly_moods[month] = []
            monthly_moods[month].append(entry['mood_score'])
        
        # Calculate monthly averages
        monthly_averages = {}
        for month, scores in monthly_moods.items():
            if scores:
                monthly_averages[month] = {
                    'average': statistics.mean(scores),
                    'count': len(scores),
                    'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0
                }
        
        # Detect seasonal patterns
        seasonal_analysis = self._detect_seasonal_patterns(monthly_averages)
        
        # Calculate SAD risk
        sad_risk = self._calculate_sad_risk(monthly_averages, recent_data)
        
        # Generate recommendations
        recommendations = self._generate_seasonal_recommendations(seasonal_analysis, sad_risk)
        
        return {
            'monthly_averages': monthly_averages,
            'seasonal_patterns': seasonal_analysis,
            'sad_risk': sad_risk,
            'recommendations': recommendations,
            'analysis_period': f'{days} days',
            'data_points': len(recent_data)
        }
    
    def _detect_seasonal_patterns(self, monthly_averages: Dict) -> Dict:
        """Detect seasonal mood patterns"""
        patterns = {
            'winter_depression': False,
            'summer_depression': False,
            'spring_improvement': False,
            'autumn_decline': False,
            'pattern_strength': 'weak'
        }
        
        if len(monthly_averages) < 6:
            return patterns
        
        # Calculate seasonal averages
        seasonal_avgs = {}
        for season, months in self.seasonal_months.items():
            season_scores = []
            for month in months:
                if month in monthly_averages:
                    season_scores.append(monthly_averages[month]['average'])
            
            if season_scores:
                seasonal_avgs[season] = statistics.mean(season_scores)
        
        if len(seasonal_avgs) < 2:
            return patterns
        
        # Check for winter depression (SAD)
        if 'winter' in seasonal_avgs and 'summer' in seasonal_avgs:
            winter_summer_diff = seasonal_avgs['summer'] - seasonal_avgs['winter']
            if winter_summer_diff >= 1.5:  # Significant difference
                patterns['winter_depression'] = True
                patterns['pattern_strength'] = 'strong' if winter_summer_diff >= 2.5 else 'moderate'
        
        # Check for summer depression (reverse SAD)
        if 'summer' in seasonal_avgs and 'winter' in seasonal_avgs:
            summer_winter_diff = seasonal_avgs['winter'] - seasonal_avgs['summer']
            if summer_winter_diff >= 1.5:
                patterns['summer_depression'] = True
                patterns['pattern_strength'] = 'strong' if summer_winter_diff >= 2.5 else 'moderate'
        
        # Check for spring improvement
        if 'spring' in seasonal_avgs and 'winter' in seasonal_avgs:
            spring_winter_diff = seasonal_avgs['spring'] - seasonal_avgs['winter']
            if spring_winter_diff >= 1.0:
                patterns['spring_improvement'] = True
        
        # Check for autumn decline
        if 'autumn' in seasonal_avgs and 'summer' in seasonal_avgs:
            summer_autumn_diff = seasonal_avgs['summer'] - seasonal_avgs['autumn']
            if summer_autumn_diff >= 1.0:
                patterns['autumn_decline'] = True
        
        return patterns
    
    def _calculate_sad_risk(self, monthly_averages: Dict, mood_data: List[Dict]) -> Dict:
        """Calculate Seasonal Affective Disorder risk"""
        risk_factors = {
            'seasonal_pattern': 0,
            'winter_low': 0,
            'symptom_frequency': 0,
            'overall_risk': 'low'
        }
        
        # Check for winter depression pattern
        if 'winter' in monthly_averages and 'summer' in monthly_averages:
            winter_avg = monthly_averages['winter']['average']
            summer_avg = monthly_averages['summer']['average']
            
            if winter_avg < summer_avg:
                risk_factors['seasonal_pattern'] = min(10, (summer_avg - winter_avg) * 2)
            
            if winter_avg <= 4:  # Low mood in winter
                risk_factors['winter_low'] = min(10, (5 - winter_avg) * 2)
        
        # Check for SAD symptoms in mood data
        # This would require additional symptom tracking data
        # For now, estimate based on mood patterns
        low_mood_entries = [entry for entry in mood_data if entry['mood_score'] <= 4]
        if low_mood_entries:
            risk_factors['symptom_frequency'] = min(10, len(low_mood_entries) / len(mood_data) * 10)
        
        # Calculate overall risk
        total_risk = sum(risk_factors.values()) / 3  # Average of risk factors
        
        if total_risk >= 7:
            risk_factors['overall_risk'] = 'high'
        elif total_risk >= 4:
            risk_factors['overall_risk'] = 'moderate'
        else:
            risk_factors['overall_risk'] = 'low'
        
        return risk_factors
    
    def _generate_seasonal_recommendations(self, patterns: Dict, sad_risk: Dict) -> List[Dict]:
        """Generate seasonal recommendations based on patterns"""
        recommendations = []
        
        # Winter depression recommendations
        if patterns.get('winter_depression'):
            recommendations.append({
                'type': 'light_therapy',
                'priority': 'high',
                'title': 'Light Therapy',
                'description': 'Consider using a light therapy box for 30 minutes each morning',
                'implementation': 'Start with 10,000 lux light box, gradually increase exposure',
                'evidence': 'Proven effective for Seasonal Affective Disorder'
            })
            
            recommendations.append({
                'type': 'vitamin_d',
                'priority': 'medium',
                'title': 'Vitamin D Supplementation',
                'description': 'Consider vitamin D supplements during winter months',
                'implementation': 'Consult with healthcare provider for appropriate dosage',
                'evidence': 'May help with mood regulation in winter'
            })
        
        # Summer depression recommendations
        if patterns.get('summer_depression'):
            recommendations.append({
                'type': 'cooling_strategies',
                'priority': 'high',
                'title': 'Cooling and Shade',
                'description': 'Stay in cool, shaded areas during peak sun hours',
                'implementation': 'Use air conditioning, fans, and light clothing',
                'evidence': 'Heat sensitivity can worsen summer depression'
            })
        
        # General seasonal recommendations
        if patterns.get('pattern_strength') in ['moderate', 'strong']:
            recommendations.append({
                'type': 'seasonal_planning',
                'priority': 'medium',
                'title': 'Seasonal Activity Planning',
                'description': 'Plan activities that match your seasonal mood patterns',
                'implementation': 'Schedule more indoor activities in difficult seasons',
                'evidence': 'Adapting activities to mood patterns can help'
            })
            
            recommendations.append({
                'type': 'professional_help',
                'priority': 'high' if sad_risk.get('overall_risk') == 'high' else 'medium',
                'title': 'Professional Support',
                'description': 'Consider consulting a mental health professional about seasonal patterns',
                'implementation': 'Schedule appointment before difficult season begins',
                'evidence': 'Early intervention is most effective for seasonal depression'
            })
        
        # SAD-specific recommendations
        if sad_risk.get('overall_risk') in ['moderate', 'high']:
            recommendations.append({
                'type': 'sleep_hygiene',
                'priority': 'medium',
                'title': 'Sleep Schedule Regulation',
                'description': 'Maintain consistent sleep schedule, especially in winter',
                'implementation': 'Go to bed and wake up at same time daily, even on weekends',
                'evidence': 'Regular sleep helps regulate circadian rhythms'
            })
            
            recommendations.append({
                'type': 'social_connection',
                'priority': 'medium',
                'title': 'Maintain Social Connections',
                'description': 'Stay connected with friends and family during difficult seasons',
                'implementation': 'Schedule regular social activities, even if you don\'t feel like it',
                'evidence': 'Social support buffers against seasonal depression'
            })
        
        return recommendations
    
    def predict_seasonal_mood(self, user_id: int, target_date: date) -> Dict:
        """Predict mood for a specific date based on seasonal patterns"""
        # This would integrate with user's historical data
        # For now, provide a template structure
        
        target_month = target_date.month
        season = None
        
        for season_name, months in self.seasonal_months.items():
            if target_month in months:
                season = season_name
                break
        
        # Base prediction on seasonal patterns
        seasonal_predictions = {
            'winter': {'predicted_mood': 5.5, 'confidence': 0.6, 'risk_factors': ['low_light', 'cold_weather']},
            'spring': {'predicted_mood': 6.8, 'confidence': 0.7, 'risk_factors': ['allergies']},
            'summer': {'predicted_mood': 7.2, 'confidence': 0.8, 'risk_factors': ['heat_sensitivity']},
            'autumn': {'predicted_mood': 6.0, 'confidence': 0.6, 'risk_factors': ['daylight_reduction']}
        }
        
        if season:
            prediction = seasonal_predictions[season]
            prediction['season'] = season
            prediction['target_date'] = target_date.isoformat()
            return prediction
        
        return {'error': 'Unable to predict mood for this date'}
    
    def get_seasonal_insights(self, user_id: int) -> Dict:
        """Get personalized seasonal insights for user"""
        # This would integrate with user's data
        # For now, provide template insights
        
        current_season = self._get_current_season()
        
        insights = {
            'current_season': current_season,
            'seasonal_tips': self._get_seasonal_tips(current_season),
            'upcoming_challenges': self._get_upcoming_challenges(current_season),
            'preparation_suggestions': self._get_preparation_suggestions(current_season)
        }
        
        return insights
    
    def _get_current_season(self) -> str:
        """Get current season based on date"""
        current_month = datetime.now().month
        
        for season, months in self.seasonal_months.items():
            if current_month in months:
                return season
        
        return 'unknown'
    
    def _get_seasonal_tips(self, season: str) -> List[str]:
        """Get seasonal tips for current season"""
        tips = {
            'winter': [
                'Get as much natural light as possible during the day',
                'Consider light therapy if you feel consistently low',
                'Maintain regular sleep schedule',
                'Stay active with indoor exercises',
                'Connect with friends and family regularly'
            ],
            'spring': [
                'Take advantage of increasing daylight',
                'Spend time outdoors when possible',
                'Start new projects or hobbies',
                'Be patient with mood fluctuations',
                'Plan enjoyable activities'
            ],
            'summer': [
                'Stay cool and hydrated',
                'Avoid peak sun hours if heat affects your mood',
                'Maintain social connections',
                'Plan indoor activities for hot days',
                'Take advantage of longer days'
            ],
            'autumn': [
                'Prepare for shorter days',
                'Maintain regular routines',
                'Plan indoor activities you enjoy',
                'Stay connected with support system',
                'Consider light therapy as days get shorter'
            ]
        }
        
        return tips.get(season, [])
    
    def _get_upcoming_challenges(self, season: str) -> List[str]:
        """Get upcoming seasonal challenges"""
        challenges = {
            'winter': ['Shorter days', 'Cold weather', 'Holiday stress', 'Reduced sunlight'],
            'spring': ['Weather changes', 'Allergies', 'Academic pressure', 'Social expectations'],
            'summer': ['Heat sensitivity', 'Vacation planning', 'Social pressure', 'Body image concerns'],
            'autumn': ['Daylight reduction', 'Back to school stress', 'Weather changes', 'Holiday preparation']
        }
        
        return challenges.get(season, [])
    
    def _get_preparation_suggestions(self, season: str) -> List[str]:
        """Get preparation suggestions for upcoming season"""
        suggestions = {
            'winter': [
                'Set up light therapy box',
                'Plan indoor activities',
                'Schedule regular social time',
                'Prepare for holiday stress',
                'Maintain exercise routine'
            ],
            'spring': [
                'Plan outdoor activities',
                'Prepare for academic pressure',
                'Set realistic goals',
                'Plan social activities',
                'Prepare for weather changes'
            ],
            'summer': [
                'Plan cooling strategies',
                'Schedule indoor activities',
                'Prepare for social events',
                'Plan vacation activities',
                'Maintain hydration routine'
            ],
            'autumn': [
                'Prepare for shorter days',
                'Plan indoor hobbies',
                'Schedule regular check-ins',
                'Prepare for academic stress',
                'Set up light therapy if needed'
            ]
        }
        
        return suggestions.get(season, [])

# Global instance
seasonal_tracker = SeasonalTracker()
