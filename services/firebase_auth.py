"""
Firebase Authentication Service for WellnessWeavers
Handles Firebase authentication integration with Flask-Login
"""

from flask import current_app, request, session
from flask_login import login_user, logout_user, current_user
from datetime import datetime
import logging

from models import User
from database import db
from firebase_config import firebase_config

logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Service for handling Firebase authentication"""
    
    def __init__(self):
        self.firebase = firebase_config
    
    def verify_firebase_token(self, id_token):
        """Verify Firebase ID token and return user data"""
        try:
            # Check if Firebase is properly initialized
            if not self.firebase.auth_client:
                logger.warning("Firebase not initialized, skipping token verification")
                return None
            
            # Verify the token with Firebase
            decoded_token = self.firebase.verify_id_token(id_token)
            
            if not decoded_token:
                return None
            
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'phone_number': decoded_token.get('phone_number'),
                'firebase': decoded_token.get('firebase', {})
            }
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return None
    
    def authenticate_user(self, id_token):
        """Authenticate user with Firebase token"""
        try:
            # Verify Firebase token
            firebase_user_data = self.verify_firebase_token(id_token)
            
            if not firebase_user_data:
                return None
            
            # Check if user exists in our database
            user = User.get_by_firebase_uid(firebase_user_data['uid'])
            
            if not user:
                # Create new user from Firebase data
                user = User.create_from_firebase(firebase_user_data)
                
                # Generate unique username if needed
                if not user.username or User.query.filter_by(username=user.username).first():
                    base_username = user.email.split('@')[0] if user.email else 'user'
                    counter = 1
                    while User.query.filter_by(username=user.username).first():
                        user.username = f"{base_username}{counter}"
                        counter += 1
                
                db.session.add(user)
                db.session.commit()
                
                logger.info(f"Created new user from Firebase: {user.username}")
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            
            # Update user data from Firebase if needed
            if firebase_user_data.get('email') and firebase_user_data['email'] != user.email:
                user.email = firebase_user_data['email']
            
            if firebase_user_data.get('name') and firebase_user_data['name'] != user.full_name:
                user.full_name = firebase_user_data['name']
            
            if firebase_user_data.get('email_verified') and not user.is_verified:
                user.is_verified = True
                user.email_verified_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log in the user
            login_user(user, remember=True)
            
            return user
            
        except Exception as e:
            logger.error(f"Firebase authentication failed: {e}")
            return None
    
    def create_custom_token(self, user_id, additional_claims=None):
        """Create custom Firebase token for user"""
        try:
            user = User.query.get(user_id)
            if not user or not user.firebase_uid:
                return None
            
            return self.firebase.create_custom_token(user.firebase_uid, additional_claims)
        except Exception as e:
            logger.error(f"Custom token creation failed: {e}")
            return None
    
    def set_user_claims(self, user_id, claims):
        """Set custom claims for Firebase user"""
        try:
            user = User.query.get(user_id)
            if not user or not user.firebase_uid:
                return False
            
            return self.firebase.set_custom_user_claims(user.firebase_uid, claims)
        except Exception as e:
            logger.error(f"Set user claims failed: {e}")
            return False
    
    def delete_firebase_user(self, user_id):
        """Delete user from Firebase Auth"""
        try:
            user = User.query.get(user_id)
            if not user or not user.firebase_uid:
                return False
            
            return self.firebase.delete_user(user.firebase_uid)
        except Exception as e:
            logger.error(f"Delete Firebase user failed: {e}")
            return False
    
    def get_firebase_user_data(self, user_id):
        """Get Firebase user data"""
        try:
            user = User.query.get(user_id)
            if not user or not user.firebase_uid:
                return None
            
            return self.firebase.get_user_by_uid(user.firebase_uid)
        except Exception as e:
            logger.error(f"Get Firebase user data failed: {e}")
            return None
    
    def sync_user_data_to_firestore(self, user_id):
        """Sync user data to Firestore for real-time features"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Prepare user data for Firestore
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'wellness_score': user.wellness_score,
                'total_points': user.total_points,
                'streak_days': user.streak_days,
                'level': user.level,
                'subscription_tier': user.subscription_tier,
                'is_active': user.is_active,
                'last_activity': user.last_activity.isoformat() if user.last_activity else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            
            # Store in Firestore
            return self.firebase.set_firestore_document('users', str(user.id), user_data)
        except Exception as e:
            logger.error(f"Sync user data to Firestore failed: {e}")
            return False
    
    def get_firestore_user_data(self, user_id):
        """Get user data from Firestore"""
        try:
            return self.firebase.get_firestore_document('users', str(user_id))
        except Exception as e:
            logger.error(f"Get Firestore user data failed: {e}")
            return None
    
    def update_firestore_user_data(self, user_id, data):
        """Update user data in Firestore"""
        try:
            return self.firebase.update_firestore_document('users', str(user_id), data)
        except Exception as e:
            logger.error(f"Update Firestore user data failed: {e}")
            return False
    
    def handle_firebase_auth_error(self, error):
        """Handle Firebase authentication errors"""
        error_messages = {
            'auth/user-not-found': 'User not found',
            'auth/wrong-password': 'Incorrect password',
            'auth/invalid-email': 'Invalid email address',
            'auth/user-disabled': 'User account has been disabled',
            'auth/too-many-requests': 'Too many failed attempts. Please try again later',
            'auth/network-request-failed': 'Network error. Please check your connection',
            'auth/invalid-credential': 'Invalid credentials',
            'auth/email-already-in-use': 'Email is already in use',
            'auth/weak-password': 'Password is too weak',
            'auth/operation-not-allowed': 'This sign-in method is not enabled'
        }
        
        error_code = getattr(error, 'code', str(error))
        return error_messages.get(error_code, 'Authentication failed')
    
    def get_pyrebase_config(self):
        """Get Pyrebase configuration for client-side operations"""
        return self.firebase.pyrebase_config
    
    def get_pyrebase_auth(self):
        """Get Pyrebase auth instance for client-side operations"""
        return self.firebase.get_pyrebase_auth()
    
    def get_pyrebase_database(self):
        """Get Pyrebase database instance"""
        return self.firebase.get_pyrebase_database()
    
    def get_pyrebase_storage(self):
        """Get Pyrebase storage instance"""
        return self.firebase.get_pyrebase_storage()

# Global Firebase auth service instance
firebase_auth_service = FirebaseAuthService()
