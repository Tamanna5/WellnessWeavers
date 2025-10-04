#!/usr/bin/env python3
"""
WellnessWeavers - AI-Powered Mental Health Support Platform
Main Flask Application
"""
from models import User
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
import os
from datetime import datetime

# Import configuration
from config import Config

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
mail = Mail(app)
cors = CORS(app)

# Import models after app is created
with app.app_context():
    from models import (
        User, Mood, MoodPattern, Conversation, Achievement, VoiceJournal,
        HabitTracker, HabitEntry, Medication, MedicationLog,
        Therapist, TherapySession, Goal, Milestone,
        SupportGroup, GroupMembership, GroupPost,
        CrisisAlert, EmergencyContact, SleepLog, ActivityLog, 
        SocialInteraction, SafetyPlan
    )

# Import and register routes after models are available
def register_routes():
    from routes.auth import auth_bp
    # from routes.dashboard import dashboard_bp
    # from routes.api import api_bp
    # from routes.pages import pages_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    # app.register_blueprint(api_bp, url_prefix='/api')
    # app.register_blueprint(pages_bp)

register_routes()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Main landing page route
@app.route('/')
def index():
    return render_template('index.html')

# Health check endpoint
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }

# Context processors for global template variables
@app.context_processor
def inject_global_vars():
    return {
        'current_year': datetime.now().year,
        'app_name': 'WellnessWeavers'
    }

# CLI commands
@app.cli.command()
def create_db():
    """Create database tables."""
    db.create_all()
    print("Database tables created successfully!")

@app.cli.command()
def reset_db():
    """Reset database tables."""
    db.drop_all()
    db.create_all()
    print("Database reset successfully!")

@app.cli.command()
def seed_db():
    """Seed database with sample data."""
    # Add sample achievements
    achievements = [
        Achievement(
            name="First Steps",
            description="Complete your first mood entry",
            icon="fa-walking",
            points=10
        ),
        Achievement(
            name="Week Warrior",
            description="Track your mood for 7 consecutive days",
            icon="fa-calendar-week",
            points=50
        ),
        Achievement(
            name="Chat Champion",
            description="Have 10 conversations with your AI companion",
            icon="fa-comments",
            points=25
        ),
        Achievement(
            name="Mindful Master",
            description="Complete 5 meditation sessions",
            icon="fa-lotus-position",
            points=30
        )
    ]
    
    for achievement in achievements:
        db.session.add(achievement)
    
    try:
        db.session.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {str(e)}")

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )