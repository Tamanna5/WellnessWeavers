"""
Background Tasks for WellnessWeavers
Scheduled tasks and background processing
"""

import os
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from database import db
from models import User, Mood, Achievement, CrisisAlert
from services.notification_service import notification_service
from services.crisis_detection import crisis_detection_service
from utils.data_processor import data_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manager for background tasks and scheduled jobs"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background task scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Background task manager started")
    
    def stop(self):
        """Stop background task scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Background task manager stopped")
    
    def _run_scheduler(self):
        """Run the task scheduler"""
        # Schedule daily tasks
        schedule.every().day.at("09:00").do(self._send_daily_reminders)
        schedule.every().day.at("18:00").do(self._send_evening_check_ins)
        schedule.every().monday.at("10:00").do(self._send_weekly_summaries)
        schedule.every().day.at("00:00").do(self._cleanup_old_data)
        schedule.every().hour.do(self._check_crisis_alerts)
        
        # Run scheduler
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _send_daily_reminders(self):
        """Send daily mood tracking reminders"""
        logger.info("Sending daily mood reminders")
        
        try:
            # Get users who haven't logged mood today
            today = datetime.utcnow().date()
            users_without_mood = db.session.query(User).filter(
                ~User.id.in_(
                    db.session.query(Mood.user_id).filter(
                        db.func.date(Mood.created_at) == today
                    )
                ),
                User.is_active == True,
                User.email_notifications == True
            ).all()
            
            for user in users_without_mood:
                try:
                    notification_service.send_mood_reminder(
                        user.email, 
                        user.full_name or user.username,
                        user.streak_days
                    )
                    logger.info(f"Sent mood reminder to {user.email}")
                except Exception as e:
                    logger.error(f"Error sending reminder to {user.email}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in daily reminders task: {str(e)}")
    
    def _send_evening_check_ins(self):
        """Send evening check-in messages"""
        logger.info("Sending evening check-ins")
        
        try:
            # Get users who logged mood today
            today = datetime.utcnow().date()
            users_with_mood = db.session.query(User).join(Mood).filter(
                db.func.date(Mood.created_at) == today,
                User.is_active == True,
                User.email_notifications == True
            ).distinct().all()
            
            for user in users_with_mood:
                try:
                    # Get today's mood
                    today_mood = Mood.query.filter(
                        Mood.user_id == user.id,
                        db.func.date(Mood.created_at) == today
                    ).first()
                    
                    if today_mood and today_mood.mood_score <= 4:
                        # Send supportive message for low mood
                        notification_service.send_email(
                            user.email,
                            "Evening Check-in - How are you feeling?",
                            f"""
                            <html>
                            <body>
                                <h2>Evening Check-in</h2>
                                <p>Hi {user.full_name or user.username},</p>
                                <p>I noticed you were feeling a bit down earlier today. How are you doing now?</p>
                                <p>Remember, it's okay to have difficult days, and you're not alone in this.</p>
                                <p>If you need someone to talk to, I'm here for you.</p>
                                <p>Take care,<br>Your WellnessWeavers Team</p>
                            </body>
                            </html>
                            """
                        )
                        logger.info(f"Sent supportive check-in to {user.email}")
                
                except Exception as e:
                    logger.error(f"Error sending check-in to {user.email}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in evening check-ins task: {str(e)}")
    
    def _send_weekly_summaries(self):
        """Send weekly wellness summaries"""
        logger.info("Sending weekly summaries")
        
        try:
            # Get active users
            active_users = User.query.filter(
                User.is_active == True,
                User.email_notifications == True
            ).all()
            
            for user in active_users:
                try:
                    # Get last week's data
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    recent_moods = Mood.query.filter(
                        Mood.user_id == user.id,
                        Mood.created_at >= week_ago
                    ).all()
                    
                    if recent_moods:
                        # Calculate weekly summary
                        mood_scores = [mood.mood_score for mood in recent_moods]
                        avg_mood = sum(mood_scores) / len(mood_scores)
                        
                        summary_data = {
                            'week_date': week_ago.strftime('%B %d, %Y'),
                            'mood_entries': len(recent_moods),
                            'average_mood': round(avg_mood, 1),
                            'streak_days': user.streak_days,
                            'wellness_score': user.wellness_score,
                            'insights': 'Keep up the great work on your wellness journey!'
                        }
                        
                        notification_service.send_weekly_summary(
                            user.email,
                            user.full_name or user.username,
                            summary_data
                        )
                        logger.info(f"Sent weekly summary to {user.email}")
                
                except Exception as e:
                    logger.error(f"Error sending weekly summary to {user.email}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in weekly summaries task: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old data to maintain performance"""
        logger.info("Cleaning up old data")
        
        try:
            # Delete old crisis alerts (older than 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_alerts = CrisisAlert.query.filter(
                CrisisAlert.detected_at < cutoff_date
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            db.session.commit()
            logger.info(f"Cleaned up {len(old_alerts)} old crisis alerts")
        
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")
            db.session.rollback()
    
    def _check_crisis_alerts(self):
        """Check for active crisis alerts that need follow-up"""
        logger.info("Checking crisis alerts")
        
        try:
            # Get active crisis alerts from last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_alerts = CrisisAlert.query.filter(
                CrisisAlert.detected_at >= yesterday,
                CrisisAlert.status == 'active'
            ).all()
            
            for alert in active_alerts:
                # Check if intervention was triggered
                if not alert.intervention_triggered:
                    # Trigger intervention
                    crisis_detection_service._trigger_intervention(alert)
                    logger.info(f"Triggered intervention for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Error in crisis alert check: {str(e)}")
    
    def send_achievement_notifications(self, user_id: int, achievements: List[Dict]):
        """Send achievement notifications to user"""
        try:
            user = User.query.get(user_id)
            if not user or not user.email_notifications:
                return
            
            for achievement in achievements:
                notification_service.send_achievement_notification(
                    user.email,
                    user.full_name or user.username,
                    achievement
                )
                logger.info(f"Sent achievement notification to {user.email}")
        
        except Exception as e:
            logger.error(f"Error sending achievement notifications: {str(e)}")
    
    def process_user_insights(self, user_id: int):
        """Process insights for a specific user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return
            
            # Get recent mood data
            recent_moods = Mood.query.filter(
                Mood.user_id == user.id
            ).order_by(Mood.created_at.desc()).limit(30).all()
            
            if not recent_moods:
                return
            
            # Process mood data
            mood_data = [{'mood_score': mood.mood_score, 'created_at': mood.created_at} for mood in recent_moods]
            analysis = data_processor.analyze_mood_patterns(mood_data)
            
            # Update user's wellness score
            new_score = data_processor.calculate_wellness_score(analysis)
            user.wellness_score = new_score
            
            # Check for achievements
            new_achievements = Achievement.check_and_award_achievements(user)
            
            # Send achievement notifications
            if new_achievements:
                achievement_data = [achievement.to_dict() for achievement in new_achievements]
                self.send_achievement_notifications(user.id, achievement_data)
            
            db.session.commit()
            logger.info(f"Processed insights for user {user.id}")
        
        except Exception as e:
            logger.error(f"Error processing user insights: {str(e)}")
            db.session.rollback()

# Global instance
background_task_manager = BackgroundTaskManager()

# Task decorators for easy scheduling
def daily_task(time_str: str):
    """Decorator for daily tasks"""
    def decorator(func):
        schedule.every().day.at(time_str).do(func)
        return func
    return decorator

def weekly_task(day: str, time_str: str):
    """Decorator for weekly tasks"""
    def decorator(func):
        getattr(schedule.every(), day).at(time_str).do(func)
        return func
    return decorator

def hourly_task():
    """Decorator for hourly tasks"""
    def decorator(func):
        schedule.every().hour.do(func)
        return func
    return decorator

# Example task functions
@daily_task("08:00")
def send_morning_motivation():
    """Send morning motivation messages"""
    logger.info("Sending morning motivation messages")
    # Implementation here

@weekly_task("monday", "09:00")
def send_weekly_goals():
    """Send weekly goal reminders"""
    logger.info("Sending weekly goal reminders")
    # Implementation here

@hourly_task()
def check_system_health():
    """Check system health and performance"""
    logger.info("Checking system health")
    # Implementation here
