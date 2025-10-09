"""
Authentication routes for WellnessWeavers
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta

from models import User
from database import db
from services.firebase_auth import firebase_auth_service

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        age = request.form.get('age', '').strip()
        preferred_language = request.form.get('preferred_language', 'en')
        terms_accepted = request.form.get('terms_accepted') == 'on'
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Please enter a valid email address")
        
        if not password:
            errors.append("Password is required")
        else:
            is_valid, message = validate_password(password)
            if not is_valid:
                errors.append(message)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not first_name:
            errors.append("First name is required")
        
        if not last_name:
            errors.append("Last name is required")
        
        if not age or not age.isdigit() or int(age) < 13 or int(age) > 120:
            errors.append("Please enter a valid age (13-120)")
        
        if not terms_accepted:
            errors.append("You must accept the Terms of Service")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                age=int(age),
                preferred_language=preferred_language
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Validation
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/login.html')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'error')
            return render_template('auth/login.html')
        
        # Login user
        login_user(user, remember=remember_me)
        user.last_login = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Login update error: {str(e)}")
        
        flash(f'Welcome back, {user.first_name}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - request reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # TODO: Implement email sending for password reset
            # For now, just show a message
            flash('If an account with this email exists, you will receive password reset instructions.', 'info')
        else:
            # Still show success message for security
            flash('If an account with this email exists, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>')
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # TODO: Implement token verification and password reset
    flash('Password reset functionality is not yet implemented', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    # TODO: Implement email verification
    flash('Email verification functionality is not yet implemented', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    """Resend email verification"""
    # TODO: Implement email verification resend
    flash('Email verification resend functionality is not yet implemented', 'info')
    return redirect(url_for('dashboard.index'))

# Firebase Authentication Routes
@auth_bp.route('/firebase/login', methods=['POST'])
def firebase_login():
    """Firebase authentication login"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Authenticate user with Firebase
        user = firebase_auth_service.authenticate_user(id_token)
        
        if not user:
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Sync user data to Firestore
        firebase_auth_service.sync_user_data_to_firestore(user.id)
        
        return jsonify({
            'success': True,
            'user': user.to_dict(include_sensitive=False),
            'message': f'Welcome back, {user.full_name or user.username}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/firebase/register', methods=['POST'])
def firebase_register():
    """Firebase authentication registration"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        additional_data = data.get('additionalData', {})
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Authenticate user with Firebase
        user = firebase_auth_service.authenticate_user(id_token)
        
        if not user:
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Update user with additional data if provided
        if additional_data:
            if 'username' in additional_data:
                user.username = additional_data['username']
            if 'age_range' in additional_data:
                user.age_range = additional_data['age_range']
            if 'gender' in additional_data:
                user.gender = additional_data['gender']
            if 'cultural_background' in additional_data:
                user.cultural_background = additional_data['cultural_background']
            if 'location_city' in additional_data:
                user.location_city = additional_data['location_city']
            
            db.session.commit()
        
        # Sync user data to Firestore
        firebase_auth_service.sync_user_data_to_firestore(user.id)
        
        return jsonify({
            'success': True,
            'user': user.to_dict(include_sensitive=False),
            'message': f'Welcome to WellnessWeavers, {user.full_name or user.username}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/firebase/config')
def firebase_config():
    """Get Firebase configuration for client-side"""
    try:
        config = firebase_auth_service.get_pyrebase_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/firebase/custom-token')
@login_required
def firebase_custom_token():
    """Get custom Firebase token for current user"""
    try:
        additional_claims = {
            'subscription_tier': current_user.subscription_tier,
            'wellness_score': current_user.wellness_score,
            'level': current_user.level
        }
        
        custom_token = firebase_auth_service.create_custom_token(
            current_user.id, 
            additional_claims
        )
        
        if not custom_token:
            return jsonify({'error': 'Failed to create custom token'}), 500
        
        return jsonify({
            'success': True,
            'customToken': custom_token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/firebase/sync')
@login_required
def firebase_sync():
    """Sync current user data to Firestore"""
    try:
        success = firebase_auth_service.sync_user_data_to_firestore(current_user.id)
        
        if not success:
            return jsonify({'error': 'Failed to sync data'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Data synced successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500