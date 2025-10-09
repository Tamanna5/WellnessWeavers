"""
Cognitive Distortion Detection Service for WellnessWeavers
Detect and gently correct thinking errors in user conversations and journal entries
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CognitiveDistortionDetector:
    """Service for detecting cognitive distortions in user text"""
    
    def __init__(self):
        self.distortion_patterns = self._compile_distortion_patterns()
        self.cultural_patterns = self._compile_cultural_patterns()
    
    def _compile_distortion_patterns(self) -> Dict[str, Dict]:
        """Compile regex patterns for cognitive distortions"""
        return {
            'all_or_nothing': {
                'patterns': [
                    r'\b(always|never|everyone|nobody|all|none|every|nothing)\b',
                    r'\b(perfect|complete|total|entire)\b',
                    r'\b(impossible|hopeless|useless|worthless)\b'
                ],
                'description': 'Seeing things in black and white, no shades of gray',
                'example': 'I always fail at everything'
            },
            'overgeneralization': {
                'patterns': [
                    r'\b(always|never|every time|all the time|constantly)\b',
                    r'\b(everyone|nobody|everybody|no one)\b',
                    r'\b(typical|usual|normal)\b'
                ],
                'description': 'Making broad generalizations from limited experiences',
                'example': 'I never do anything right'
            },
            'mental_filter': {
                'patterns': [
                    r'\b(but|however|except|although|despite)\b',
                    r'\b(only|just|merely|simply)\b',
                    r'\b(ignoring|forgetting|overlooking)\b'
                ],
                'description': 'Focusing only on negative details while ignoring positive ones',
                'example': 'I got a B+ but I should have gotten an A'
            },
            'mind_reading': {
                'patterns': [
                    r'\b(they think|they believe|they feel|they know)\b',
                    r'\b(probably|obviously|clearly|definitely)\b',
                    r'\b(they must|they should|they will)\b'
                ],
                'description': 'Assuming you know what others are thinking without evidence',
                'example': 'They think I\'m stupid'
            },
            'fortune_telling': {
                'patterns': [
                    r'\b(will never|will always|going to|about to)\b',
                    r'\b(inevitable|certain|guaranteed)\b',
                    r'\b(predict|know for sure|definitely will)\b'
                ],
                'description': 'Predicting negative outcomes without evidence',
                'example': 'I will never succeed'
            },
            'catastrophizing': {
                'patterns': [
                    r'\b(disaster|terrible|awful|horrible|worst)\b',
                    r'\b(end of the world|ruined|destroyed)\b',
                    r'\b(can\'t handle|unbearable|intolerable)\b'
                ],
                'description': 'Exaggerating the importance of negative events',
                'example': 'This is a disaster, my life is ruined'
            },
            'should_statements': {
                'patterns': [
                    r'\b(should|must|have to|ought to|need to)\b',
                    r'\b(required|obligated|expected)\b',
                    r'\b(perfect|ideal|right way)\b'
                ],
                'description': 'Using rigid rules about how things should be',
                'example': 'I should be perfect at everything'
            },
            'labeling': {
                'patterns': [
                    r'\b(i am|i\'m a|they are|he is|she is)\b',
                    r'\b(loser|failure|stupid|idiot|worthless)\b',
                    r'\b(terrible|awful|horrible|disgusting)\b'
                ],
                'description': 'Attaching negative labels to yourself or others',
                'example': 'I am a complete failure'
            },
            'personalization': {
                'patterns': [
                    r'\b(my fault|because of me|i caused|i made)\b',
                    r'\b(if only i|if i had|i should have)\b',
                    r'\b(responsible for|blame for|due to me)\b'
                ],
                'description': 'Taking responsibility for things outside your control',
                'example': 'It\'s my fault that they\'re upset'
            },
            'emotional_reasoning': {
                'patterns': [
                    r'\b(i feel|i sense|i know|i believe)\b',
                    r'\b(because i feel|since i feel|i feel so)\b',
                    r'\b(my feelings tell me|i feel like)\b'
                ],
                'description': 'Using emotions as evidence for beliefs',
                'example': 'I feel stupid, so I must be stupid'
            }
        }
    
    def _compile_cultural_patterns(self) -> Dict[str, List[str]]:
        """Compile patterns specific to Indian cultural context"""
        return {
            'academic_pressure': [
                'not good enough for my parents',
                'disappointing my family',
                'not meeting expectations',
                'wasting my parents\' money',
                'bringing shame to family'
            ],
            'family_expectations': [
                'should be more successful',
                'not living up to family name',
                'disappointing my elders',
                'not following tradition',
                'letting down my community'
            ],
            'social_comparison': [
                'everyone else is doing better',
                'all my friends are successful',
                'others have it easier',
                'i\'m the only one struggling',
                'everyone else is happy'
            ],
            'stigma_concerns': [
                'people will think i\'m weak',
                'mental health is not real',
                'i should be able to handle this',
                'therapy is for crazy people',
                'i don\'t want to be judged'
            ]
        }
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for cognitive distortions"""
        if not text:
            return {'distortions': [], 'cultural_factors': [], 'suggestions': []}
        
        text_lower = text.lower()
        distortions = []
        cultural_factors = []
        
        # Check for cognitive distortions
        for distortion_type, data in self.distortion_patterns.items():
            matches = []
            for pattern in data['patterns']:
                found_matches = re.findall(pattern, text_lower, re.IGNORECASE)
                matches.extend(found_matches)
            
            if matches:
                distortions.append({
                    'type': distortion_type,
                    'description': data['description'],
                    'example': data['example'],
                    'matches': matches,
                    'severity': len(matches),
                    'confidence': min(0.9, len(matches) * 0.3)
                })
        
        # Check for cultural factors
        for factor_type, patterns in self.cultural_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern in text_lower:
                    matches.append(pattern)
            
            if matches:
                cultural_factors.append({
                    'type': factor_type,
                    'matches': matches,
                    'severity': len(matches)
                })
        
        # Generate suggestions
        suggestions = self._generate_suggestions(distortions, cultural_factors)
        
        return {
            'distortions': distortions,
            'cultural_factors': cultural_factors,
            'suggestions': suggestions,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_suggestions(self, distortions: List[Dict], cultural_factors: List[Dict]) -> List[Dict]:
        """Generate gentle suggestions for addressing distortions"""
        suggestions = []
        
        # Distortion-based suggestions
        for distortion in distortions:
            distortion_type = distortion['type']
            
            if distortion_type == 'all_or_nothing':
                suggestions.append({
                    'type': 'cognitive_restructuring',
                    'message': 'Try thinking in shades of gray instead of black and white',
                    'question': 'What\'s a more balanced way to think about this?',
                    'technique': 'Look for exceptions to your "always" or "never" statements'
                })
            
            elif distortion_type == 'overgeneralization':
                suggestions.append({
                    'type': 'evidence_checking',
                    'message': 'Look for exceptions to your general rule',
                    'question': 'Can you think of times when this wasn\'t true?',
                    'technique': 'Challenge the "always" or "never" with specific examples'
                })
            
            elif distortion_type == 'mind_reading':
                suggestions.append({
                    'type': 'reality_checking',
                    'message': 'What evidence do you have for what others are thinking?',
                    'question': 'How do you know this is what they\'re thinking?',
                    'technique': 'Ask directly or look for behavioral evidence'
                })
            
            elif distortion_type == 'fortune_telling':
                suggestions.append({
                    'type': 'uncertainty_acceptance',
                    'message': 'You can\'t predict the future - focus on what you can control',
                    'question': 'What\'s the worst that could realistically happen?',
                    'technique': 'Challenge predictions with evidence and alternatives'
                })
            
            elif distortion_type == 'catastrophizing':
                suggestions.append({
                    'type': 'perspective_taking',
                    'message': 'Is this really as bad as it seems?',
                    'question': 'What would you tell a friend in this situation?',
                    'technique': 'Put the situation in perspective with time and context'
                })
            
            elif distortion_type == 'should_statements':
                suggestions.append({
                    'type': 'flexible_thinking',
                    'message': 'Replace "should" with "it would be nice if" or "I prefer"',
                    'question': 'What\'s a more flexible way to think about this?',
                    'technique': 'Use softer language that doesn\'t create pressure'
                })
            
            elif distortion_type == 'labeling':
                suggestions.append({
                    'type': 'behavior_vs_identity',
                    'message': 'Separate your behavior from your identity',
                    'question': 'What\'s the difference between doing something wrong and being wrong?',
                    'technique': 'Focus on specific behaviors rather than global labels'
                })
            
            elif distortion_type == 'personalization':
                suggestions.append({
                    'type': 'responsibility_boundaries',
                    'message': 'What\'s actually within your control?',
                    'question': 'What part of this situation is really your responsibility?',
                    'technique': 'Distinguish between what you can and cannot control'
                })
            
            elif distortion_type == 'emotional_reasoning':
                suggestions.append({
                    'type': 'fact_vs_feeling',
                    'message': 'Feelings are valid, but they\'re not facts',
                    'question': 'What evidence do you have beyond your feelings?',
                    'technique': 'Separate emotional experience from objective reality'
                })
        
        # Cultural factor suggestions
        for factor in cultural_factors:
            factor_type = factor['type']
            
            if factor_type == 'academic_pressure':
                suggestions.append({
                    'type': 'cultural_support',
                    'message': 'Academic success is important, but your mental health matters too',
                    'question': 'How can you balance your academic goals with self-care?',
                    'technique': 'Set realistic expectations and communicate with family'
                })
            
            elif factor_type == 'family_expectations':
                suggestions.append({
                    'type': 'family_communication',
                    'message': 'Your family wants the best for you, but you can set boundaries',
                    'question': 'How can you communicate your needs while respecting their concerns?',
                    'technique': 'Have honest conversations about your mental health needs'
                })
            
            elif factor_type == 'social_comparison':
                suggestions.append({
                    'type': 'comparison_awareness',
                    'message': 'Everyone\'s journey is different - focus on your own progress',
                    'question': 'What are your unique strengths and challenges?',
                    'technique': 'Limit social media and focus on your own goals'
                })
            
            elif factor_type == 'stigma_concerns':
                suggestions.append({
                    'type': 'stigma_challenge',
                    'message': 'Mental health is just as important as physical health',
                    'question': 'What would you tell a friend who was struggling?',
                    'technique': 'Educate yourself and others about mental health'
                })
        
        return suggestions
    
    def generate_gentle_response(self, analysis: Dict) -> str:
        """Generate a gentle response to detected distortions"""
        distortions = analysis.get('distortions', [])
        cultural_factors = analysis.get('cultural_factors', [])
        
        if not distortions and not cultural_factors:
            return "Thank you for sharing your thoughts. It sounds like you're going through a difficult time."
        
        # Start with validation
        response = "I can hear that you're going through a challenging time, and your feelings are completely valid. "
        
        # Address most prominent distortion
        if distortions:
            primary_distortion = max(distortions, key=lambda x: x['severity'])
            response += f"I notice you might be thinking in a way that's making this harder for you. "
            response += f"For example, when you say things like '{primary_distortion['matches'][0]}', "
            response += f"it might be helpful to consider: {primary_distortion['description']}. "
        
        # Address cultural factors
        if cultural_factors:
            primary_factor = max(cultural_factors, key=lambda x: x['severity'])
            if primary_factor['type'] == 'academic_pressure':
                response += "I understand that academic pressure can feel overwhelming, especially with family expectations. "
                response += "Remember that your mental health is just as important as your academic success. "
            elif primary_factor['type'] == 'family_expectations':
                response += "Family expectations can feel heavy, but you deserve to prioritize your wellbeing. "
                response += "It's okay to set boundaries and communicate your needs. "
        
        # End with support
        response += "Would you like to explore some gentle ways to think about this differently?"
        
        return response
    
    def get_distortion_statistics(self, user_id: int, days: int = 30) -> Dict:
        """Get user's cognitive distortion patterns over time"""
        # This would integrate with the database to track patterns
        # For now, return a template structure
        return {
            'total_analyses': 0,
            'most_common_distortions': [],
            'cultural_factors': [],
            'improvement_trend': 'insufficient_data',
            'recommendations': []
        }

# Global instance
cognitive_distortion_detector = CognitiveDistortionDetector()
