"""
Firebase Configuration for WellnessWeavers
Handles Firebase authentication and database operations
"""

import os
import json
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
try:
    import pyrebase
except Exception:
    pyrebase = None

class FirebaseConfig:
    """Firebase configuration and authentication handler"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.auth_client = None
        self.pyrebase_config = None
        self.pyrebase_app = None
        
        # Initialize Firebase
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase credentials are available
            project_id = os.environ.get('FIREBASE_PROJECT_ID')
            if not project_id:
                print("Firebase credentials not found, using development mode")
                self._initialize_development_mode()
                return
            
            # Firebase configuration from environment variables
            firebase_config = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.environ.get('FIREBASE_CLIENT_EMAIL')}"
            }
            
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                self.app = firebase_admin.initialize_app(cred)
            
            # Initialize Firestore
            self.db = firestore.client()
            
            # Initialize Auth
            self.auth_client = auth
            
            # Pyrebase configuration for client-side operations
            self.pyrebase_config = {
                "apiKey": os.environ.get('FIREBASE_API_KEY', 'dummy-key'),
                "authDomain": f"{project_id}.firebaseapp.com",
                "databaseURL": f"https://{project_id}-default-rtdb.firebaseio.com",
                "projectId": project_id,
                "storageBucket": f"{project_id}.appspot.com",
                "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '123456789'),
                "appId": os.environ.get('FIREBASE_APP_ID', '1:123456789:web:abcdef123456')
            }
            
            # Initialize Pyrebase (optional)
            if pyrebase:
                self.pyrebase_app = pyrebase.initialize_app(self.pyrebase_config)
            else:
                self.pyrebase_app = None
            
            # Try initialize storage bucket (optional)
            try:
                self.bucket = storage.bucket()
            except Exception:
                self.bucket = None
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            # Fallback to development mode
            self._initialize_development_mode()
    
    def _initialize_development_mode(self):
        """Initialize Firebase in development mode"""
        try:
            # Development Pyrebase config (no Firebase Admin SDK in dev mode)
            self.pyrebase_config = {
                "apiKey": "AIzaSyDummyKeyForDevelopment",
                "authDomain": "wellnessweavers-dev.firebaseapp.com",
                "databaseURL": "https://wellnessweavers-dev-default-rtdb.firebaseio.com",
                "projectId": "wellnessweavers-dev",
                "storageBucket": "wellnessweavers-dev.appspot.com",
                "messagingSenderId": "123456789",
                "appId": "1:123456789:web:abcdef123456"
            }
            
            # Initialize Pyrebase for client-side operations (optional)
            if pyrebase:
                self.pyrebase_app = pyrebase.initialize_app(self.pyrebase_config)
            else:
                self.pyrebase_app = None
            
            # Set dummy values for server-side operations
            self.app = None
            self.db = None
            self.auth_client = None
            self.bucket = None
            
            print("Firebase initialized in development mode")
            
        except Exception as e:
            print(f"Firebase development mode initialization error: {e}")
            # Set all to None to prevent errors
            self.app = None
            self.db = None
            self.auth_client = None
            self.pyrebase_app = None
            self.bucket = None
    
    def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user data"""
        try:
            decoded_token = self.auth_client.verify_id_token(id_token)
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
            print(f"Token verification error: {e}")
            return None
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user data from Firebase Auth"""
        try:
            user_record = self.auth_client.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'phone_number': user_record.phone_number,
                'disabled': user_record.disabled,
                'metadata': {
                    'creation_timestamp': user_record.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp
                }
            }
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    def create_custom_token(self, uid: str, additional_claims: Dict[str, Any] = None) -> str:
        """Create custom token for user"""
        try:
            return self.auth_client.create_custom_token(uid, additional_claims)
        except Exception as e:
            print(f"Custom token creation error: {e}")
            return None
    
    def set_custom_user_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for user"""
        try:
            self.auth_client.set_custom_user_claims(uid, claims)
            return True
        except Exception as e:
            print(f"Set custom claims error: {e}")
            return False
    
    def delete_user(self, uid: str) -> bool:
        """Delete user from Firebase Auth"""
        try:
            self.auth_client.delete_user(uid)
            return True
        except Exception as e:
            print(f"Delete user error: {e}")
            return False
    
    def get_firestore_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Firestore get document error: {e}")
            return None
    
    def set_firestore_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Set document in Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data)
            return True
        except Exception as e:
            print(f"Firestore set document error: {e}")
            return False
    
    def update_firestore_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update document in Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Firestore update document error: {e}")
            return False
    
    def delete_firestore_document(self, collection: str, document_id: str) -> bool:
        """Delete document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Firestore delete document error: {e}")
            return False
    
    def get_pyrebase_auth(self):
        """Get Pyrebase auth instance for client-side operations"""
        if not self.pyrebase_app:
            raise RuntimeError('Pyrebase is not available')
        return self.pyrebase_app.auth()
    
    def get_pyrebase_database(self):
        """Get Pyrebase database instance"""
        if not self.pyrebase_app:
            raise RuntimeError('Pyrebase is not available')
        return self.pyrebase_app.database()
    
    def get_pyrebase_storage(self):
        """Get Pyrebase storage instance"""
        if not self.pyrebase_app:
            raise RuntimeError('Pyrebase is not available')
        return self.pyrebase_app.storage()

# Global Firebase instance
firebase_config = FirebaseConfig()

# Export commonly used handles with safe fallbacks
db = firebase_config.db
auth_admin = firebase_config.auth_client
bucket = getattr(firebase_config, 'bucket', None)

# Web configuration for frontend SDK (use env vars with sensible fallbacks)
# If explicit web config envs are not set, fall back to the provided values
FIREBASE_WEB_CONFIG = {
    "apiKey": os.environ.get('FIREBASE_API_KEY', "AIzaSyDjL2n1iEAQtb4QQ4rqtgAKS3R03H5GDwM"),
    "authDomain": os.environ.get('FIREBASE_AUTH_DOMAIN', "studio-6895480031-2b743.firebaseapp.com"),
    "projectId": os.environ.get('FIREBASE_PROJECT_ID', "studio-6895480031-2b743"),
    "storageBucket": os.environ.get('FIREBASE_STORAGE_BUCKET', "studio-6895480031-2b743.firebasestorage.app"),
    "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID', "717652724693"),
    "appId": os.environ.get('FIREBASE_APP_ID', "1:717652724693:web:fbeb7661ddad38b22b0b5c"),
}
