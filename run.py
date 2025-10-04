#!/usr/bin/env python3
"""
Minimal WellnessWeavers Flask App for Testing
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wellnessweavers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Simple user loader (placeholder)
@login_manager.user_loader
def load_user(user_id):
    # For now, return None since we don't have full auth yet
    return None

# Simple routes for testing
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/signup')  
def signup():
    return render_template('auth/signup.html')

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'WellnessWeavers is running!'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("🚀 Starting WellnessWeavers...")
    print("📱 Visit: http://localhost:5000")
    print("💻 Login: http://localhost:5000/login")
    print("✨ Sign Up: http://localhost:5000/signup")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )