"""
Notification Service for WellnessWeavers
Email, SMS, and push notification system
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to users"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@wellnessweavers.com')
        self.from_name = os.environ.get('FROM_NAME', 'WellnessWeavers')
        
        # SMS service configuration
        self.twilio_sid = os.environ.get('TWILIO_SID')
        self.twilio_token = os.environ.get('TWILIO_TOKEN')
        self.twilio_phone = os.environ.get('TWILIO_PHONE')
        
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None) -> bool:
        """Send email notification"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS notification"""
        try:
            if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
                logger.warning("Twilio credentials not configured")
                return False
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            
            data = {
                'From': self.twilio_phone,
                'To': to_phone,
                'Body': message
            }
            
            response = requests.post(url, data=data, auth=(self.twilio_sid, self.twilio_token))
            response.raise_for_status()
            
            logger.info(f"SMS sent successfully to {to_phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        subject = "Welcome to WellnessWeavers - Your Mental Health Journey Starts Here!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c5aa0; text-align: center;">Welcome to WellnessWeavers!</h1>
                
                <p>Hi {user_name},</p>
                
                <p>Welcome to your personal mental health support platform! We're thrilled to have you join our community of individuals committed to their wellness journey.</p>
                
                <h2 style="color: #2c5aa0;">What you can do next:</h2>
                <ul>
                    <li>📊 <strong>Track your mood</strong> - Start logging your daily emotions and patterns</li>
                    <li>🤖 <strong>Chat with our AI companion</strong> - Get 24/7 mental health support</li>
                    <li>👥 <strong>Join support groups</strong> - Connect with others on similar journeys</li>
                    <li>📈 <strong>View your analytics</strong> - Understand your mental health patterns</li>
                    <li>🏆 <strong>Earn achievements</strong> - Stay motivated with our gamification system</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wellnessweavers.com/dashboard" 
                       style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        Get Started
                    </a>
                </div>
                
                <p>Remember, taking care of your mental health is a journey, not a destination. We're here to support you every step of the way.</p>
                
                <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team.</p>
                
                <p>Best regards,<br>The WellnessWeavers Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to WellnessWeavers!
        
        Hi {user_name},
        
        Welcome to your personal mental health support platform! We're thrilled to have you join our community.
        
        What you can do next:
        - Track your mood - Start logging your daily emotions and patterns
        - Chat with our AI companion - Get 24/7 mental health support
        - Join support groups - Connect with others on similar journeys
        - View your analytics - Understand your mental health patterns
        - Earn achievements - Stay motivated with our gamification system
        
        Get started: https://wellnessweavers.com/dashboard
        
        Remember, taking care of your mental health is a journey, not a destination. We're here to support you every step of the way.
        
        Best regards,
        The WellnessWeavers Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_mood_reminder(self, user_email: str, user_name: str, streak_days: int) -> bool:
        """Send mood tracking reminder"""
        subject = f"Daily Mood Check-in - {streak_days} Day Streak! 🔥"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c5aa0; text-align: center;">Daily Mood Check-in</h1>
                
                <p>Hi {user_name},</p>
                
                <p>Great job on your {streak_days} day streak! 🎉</p>
                
                <p>How are you feeling today? Taking a moment to check in with yourself is one of the most important things you can do for your mental health.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c5aa0; margin-top: 0;">Quick Check-in Questions:</h3>
                    <ul>
                        <li>What's your mood on a scale of 1-10?</li>
                        <li>What's one thing that made you smile today?</li>
                        <li>How's your energy level?</li>
                        <lili>What would you like to focus on today?</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wellnessweavers.com/dashboard/mood/new" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        Log My Mood
                    </a>
                </div>
                
                <p>Remember, every entry helps us better understand your patterns and provide more personalized support.</p>
                
                <p>Keep up the great work! 💪</p>
                
                <p>Best regards,<br>The WellnessWeavers Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_crisis_alert(self, user_email: str, user_name: str, 
                         emergency_contacts: List[Dict]) -> bool:
        """Send crisis alert to user and emergency contacts"""
        subject = "🚨 Crisis Support - Immediate Help Available"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #dc3545; text-align: center;">Crisis Support Available</h1>
                
                <p>Hi {user_name},</p>
                
                <p>We've detected that you might be going through a difficult time. Please know that you're not alone, and help is available.</p>
                
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #721c24; margin-top: 0;">Immediate Support Resources:</h3>
                    <ul>
                        <li><strong>National Suicide Prevention Lifeline:</strong> 988</li>
                        <li><strong>Crisis Text Line:</strong> Text HOME to 741741</li>
                        <li><strong>Emergency Services:</strong> 911</li>
                    </ul>
                </div>
                
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #0c5460; margin-top: 0;">Safety Plan:</h3>
                    <ul>
                        <li>Reach out to a trusted friend or family member</li>
                        <li>Go to a safe, comfortable place</li>
                        <li>Engage in calming activities (breathing, music, etc.)</li>
                        <li>Remove any means of self-harm from your environment</li>
                    </ul>
                </div>
                
                <p>Remember: This feeling is temporary, and you are valued and important.</p>
                
                <p>If you need immediate help, please call 988 or go to your nearest emergency room.</p>
                
                <p>We care about you,<br>The WellnessWeavers Team</p>
            </div>
        </body>
        </html>
        """
        
        # Send to user
        user_sent = self.send_email(user_email, subject, html_content)
        
        # Send to emergency contacts
        for contact in emergency_contacts:
            contact_subject = f"🚨 Crisis Alert - {user_name} Needs Support"
            contact_message = f"""
            {user_name} may be experiencing a mental health crisis and could use your support.
            
            Please reach out to them and offer your support. If this is an emergency, please call 911.
            
            Crisis Resources:
            - National Suicide Prevention Lifeline: 988
            - Crisis Text Line: Text HOME to 741741
            """
            
            self.send_email(contact['email'], contact_subject, contact_message)
        
        return user_sent
    
    def send_achievement_notification(self, user_email: str, user_name: str, 
                                    achievement: Dict) -> bool:
        """Send achievement notification"""
        subject = f"🏆 Achievement Unlocked: {achievement['title']}!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ffc107; text-align: center;">🏆 Achievement Unlocked!</h1>
                
                <p>Congratulations {user_name}!</p>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <h2 style="color: #856404; margin-top: 0;">{achievement['title']}</h2>
                    <p style="font-size: 18px; margin-bottom: 0;">{achievement['description']}</p>
                    <p style="font-size: 16px; color: #856404;">+{achievement['points']} points earned!</p>
                </div>
                
                <p>You're making amazing progress on your wellness journey! Keep up the great work.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wellnessweavers.com/dashboard" 
                       style="background-color: #ffc107; color: #212529; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        View Your Progress
                    </a>
                </div>
                
                <p>Every step forward is worth celebrating! 🎉</p>
                
                <p>Best regards,<br>The WellnessWeavers Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_weekly_summary(self, user_email: str, user_name: str, 
                           summary_data: Dict) -> bool:
        """Send weekly wellness summary"""
        subject = f"Weekly Wellness Summary - {summary_data['week_date']}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c5aa0; text-align: center;">Weekly Wellness Summary</h1>
                
                <p>Hi {user_name},</p>
                
                <p>Here's your weekly wellness summary for {summary_data['week_date']}:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c5aa0; margin-top: 0;">This Week's Highlights:</h3>
                    <ul>
                        <li><strong>Mood Entries:</strong> {summary_data['mood_entries']}</li>
                        <li><strong>Average Mood:</strong> {summary_data['average_mood']}/10</li>
                        <li><strong>Streak Days:</strong> {summary_data['streak_days']}</li>
                        <li><strong>Wellness Score:</strong> {summary_data['wellness_score']}/100</li>
                    </ul>
                </div>
                
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #155724; margin-top: 0;">Insights:</h3>
                    <p>{summary_data['insights']}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wellnessweavers.com/dashboard/analytics" 
                       style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        View Detailed Analytics
                    </a>
                </div>
                
                <p>Keep up the great work on your wellness journey!</p>
                
                <p>Best regards,<br>The WellnessWeavers Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

# Global instance
notification_service = NotificationService()
