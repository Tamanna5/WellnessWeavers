#!/usr/bin/env python3
"""
Management CLI for WellnessWeavers
Command-line interface for database management, user operations, and system maintenance
"""

import os
import sys
import click
from datetime import datetime, timedelta
from flask.cli import FlaskGroup
from flask import current_app

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, Mood, Conversation, Achievement, SupportGroup
from services.notification_service import notification_service
from services.crisis_detection import crisis_detection_service
from utils.background_tasks import background_task_manager

def create_app():
    """Create Flask app for CLI"""
    return app

@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """WellnessWeavers Management CLI"""
    pass

@cli.command()
def init_db():
    """Initialize database with tables"""
    with current_app.app_context():
        db.create_all()
        click.echo("Database initialized successfully!")

@cli.command()
def reset_db():
    """Reset database (WARNING: This will delete all data!)"""
    if click.confirm("Are you sure you want to reset the database? This will delete ALL data!"):
        with current_app.app_context():
            db.drop_all()
            db.create_all()
            click.echo("Database reset successfully!")

@cli.command()
def seed_db():
    """Seed database with sample data"""
    with current_app.app_context():
        # Create sample achievements
        achievements = [
            Achievement(
                name="First Steps",
                description="Complete your first mood entry",
                icon="fa-walking",
                points=10,
                achievement_type="count",
                target_value=1,
                is_template=True
            ),
            Achievement(
                name="Week Warrior",
                description="Track your mood for 7 consecutive days",
                icon="fa-calendar-week",
                points=50,
                achievement_type="streak",
                target_value=7,
                is_template=True
            ),
            Achievement(
                name="Chat Champion",
                description="Have 10 conversations with your AI companion",
                icon="fa-comments",
                points=25,
                achievement_type="count",
                target_value=10,
                is_template=True
            ),
            Achievement(
                name="Mindful Master",
                description="Complete 5 meditation sessions",
                icon="fa-lotus-position",
                points=30,
                achievement_type="count",
                target_value=5,
                is_template=True
            )
        ]
        
        for achievement in achievements:
            db.session.add(achievement)
        
        # Create sample support groups
        support_groups = [
            SupportGroup(
                name="Anxiety Support Group",
                description="A safe space for people dealing with anxiety",
                category="anxiety",
                is_public=True,
                created_by=1,  # Assuming admin user ID 1
                status="active"
            ),
            SupportGroup(
                name="Depression Support Group",
                description="Support for those dealing with depression",
                category="depression",
                is_public=True,
                created_by=1,
                status="active"
            ),
            SupportGroup(
                name="General Wellness",
                description="General mental health and wellness discussions",
                category="general",
                is_public=True,
                created_by=1,
                status="active"
            )
        ]
        
        for group in support_groups:
            db.session.add(group)
        
        try:
            db.session.commit()
            click.echo("Database seeded successfully!")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error seeding database: {str(e)}")

@cli.command()
@click.option('--email', prompt=True, help='User email')
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.option('--full-name', prompt=True, help='Full name')
def create_user(email, username, password, full_name):
    """Create a new user"""
    with current_app.app_context():
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            click.echo("User with this email already exists!")
            return
        
        if User.query.filter_by(username=username).first():
            click.echo("User with this username already exists!")
            return
        
        # Create new user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            is_verified=True,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        click.echo(f"User {username} created successfully!")

@cli.command()
@click.option('--user-id', type=int, help='User ID to process')
@click.option('--all', is_flag=True, help='Process all users')
def process_insights(user_id, all):
    """Process insights for users"""
    with current_app.app_context():
        if all:
            users = User.query.filter_by(is_active=True).all()
            click.echo(f"Processing insights for {len(users)} users...")
            
            for user in users:
                try:
                    background_task_manager.process_user_insights(user.id)
                    click.echo(f"Processed insights for user {user.username}")
                except Exception as e:
                    click.echo(f"Error processing user {user.username}: {str(e)}")
        elif user_id:
            try:
                background_task_manager.process_user_insights(user_id)
                click.echo(f"Processed insights for user {user_id}")
            except Exception as e:
                click.echo(f"Error processing user {user_id}: {str(e)}")
        else:
            click.echo("Please specify --user-id or --all")

@cli.command()
@click.option('--days', default=30, help='Number of days to analyze')
def analyze_crisis_data(days):
    """Analyze crisis detection data"""
    with current_app.app_context():
        from models.crisis import CrisisAlert
        
        start_date = datetime.utcnow() - timedelta(days=days)
        alerts = CrisisAlert.query.filter(
            CrisisAlert.detected_at >= start_date
        ).all()
        
        if not alerts:
            click.echo("No crisis alerts found in the specified period")
            return
        
        # Analyze data
        risk_levels = {}
        for alert in alerts:
            risk_levels[alert.risk_level] = risk_levels.get(alert.risk_level, 0) + 1
        
        click.echo(f"Crisis Alert Analysis ({days} days):")
        click.echo(f"Total alerts: {len(alerts)}")
        for level, count in risk_levels.items():
            click.echo(f"  {level}: {count}")
        
        # Get intervention rate
        interventions = len([a for a in alerts if a.intervention_triggered])
        intervention_rate = (interventions / len(alerts)) * 100 if alerts else 0
        click.echo(f"Intervention rate: {intervention_rate:.1f}%")

@cli.command()
def send_test_notifications():
    """Send test notifications"""
    with current_app.app_context():
        # Get a test user
        user = User.query.first()
        if not user:
            click.echo("No users found in database")
            return
        
        try:
            # Send test email
            success = notification_service.send_welcome_email(
                user.email,
                user.full_name or user.username
            )
            
            if success:
                click.echo(f"Test notification sent to {user.email}")
            else:
                click.echo("Failed to send test notification")
        except Exception as e:
            click.echo(f"Error sending test notification: {str(e)}")

@cli.command()
@click.option('--user-id', type=int, help='User ID to check')
def check_user_data(user_id):
    """Check user data and statistics"""
    with current_app.app_context():
        if user_id:
            user = User.query.get(user_id)
            if not user:
                click.echo(f"User {user_id} not found")
                return
            
            # Get user statistics
            mood_count = Mood.query.filter_by(user_id=user.id).count()
            conversation_count = Conversation.query.filter_by(user_id=user.id).count()
            achievement_count = Achievement.query.filter_by(user_id=user.id, earned=True).count()
            
            click.echo(f"User: {user.username} ({user.email})")
            click.echo(f"  Mood entries: {mood_count}")
            click.echo(f"  Conversations: {conversation_count}")
            click.echo(f"  Achievements: {achievement_count}")
            click.echo(f"  Wellness score: {user.wellness_score}")
            click.echo(f"  Streak days: {user.streak_days}")
            click.echo(f"  Total points: {user.total_points}")
            click.echo(f"  Level: {user.level}")
        else:
            # Show overall statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            total_moods = Mood.query.count()
            total_conversations = Conversation.query.count()
            
            click.echo("System Statistics:")
            click.echo(f"  Total users: {total_users}")
            click.echo(f"  Active users: {active_users}")
            click.echo(f"  Total mood entries: {total_moods}")
            click.echo(f"  Total conversations: {total_conversations}")

@cli.command()
def cleanup_old_data():
    """Clean up old data"""
    with current_app.app_context():
        try:
            # Clean up old crisis alerts
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_alerts = CrisisAlert.query.filter(
                CrisisAlert.detected_at < cutoff_date
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            db.session.commit()
            click.echo(f"Cleaned up {len(old_alerts)} old crisis alerts")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error during cleanup: {str(e)}")

@cli.command()
def start_background_tasks():
    """Start background task manager"""
    with current_app.app_context():
        background_task_manager.start()
        click.echo("Background tasks started")

@cli.command()
def stop_background_tasks():
    """Stop background task manager"""
    background_task_manager.stop()
    click.echo("Background tasks stopped")

@cli.command()
@click.option('--text', prompt=True, help='Text to analyze')
def test_crisis_detection(text):
    """Test crisis detection on text"""
    with current_app.app_context():
        analysis = crisis_detection_service.analyze_text(text)
        
        click.echo("Crisis Detection Analysis:")
        click.echo(f"  Risk Level: {analysis['risk_level']}")
        click.echo(f"  Confidence: {analysis['confidence']:.2f}")
        click.echo(f"  Total Score: {analysis['total_score']}")
        
        if analysis['indicators']:
            click.echo("  Indicators:")
            for indicator in analysis['indicators']:
                click.echo(f"    - {indicator['category']}: {indicator['score']} matches")

if __name__ == '__main__':
    cli()
