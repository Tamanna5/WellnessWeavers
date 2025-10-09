from datetime import datetime, timedelta
import uuid

try:
    from firebase_config import db, bucket, auth_admin
    from google.cloud import firestore as gcfirestore
except Exception:
    db = None
    bucket = None
    auth_admin = None
    gcfirestore = None


class FirebaseService:
    """Abstraction over Firebase Admin SDK and Firestore operations"""

    # USER OPERATIONS
    @staticmethod
    def create_user(email, password, display_name):
        if not auth_admin:
            return {'success': False, 'error': 'Firebase auth is not configured'}
        try:
            user = auth_admin.create_user(email=email, password=password, display_name=display_name)
            if db:
                db.collection('users').document(user.uid).set({
                    'uid': user.uid,
                    'email': email,
                    'display_name': display_name,
                    'created_at': datetime.utcnow(),
                    'wellness_score': 50.0,
                    'total_points': 0,
                    'streak_days': 0,
                    'preferences': {
                        'language': 'en',
                        'chat_persona': 'Priya',
                        'notifications_enabled': True
                    },
                    'onboarding_completed': False
                })
            return {'success': True, 'uid': user.uid}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_user(uid):
        if not db:
            return None
        doc = db.collection('users').document(uid).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def update_user(uid, data):
        if not db:
            return False
        db.collection('users').document(uid).update(data)
        return True

    # CHAT
    @staticmethod
    def save_conversation(uid, message, response, metadata=None):
        if not db:
            return None
        data = {
            'user_id': uid,
            'message': message,
            'response': response,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        doc_ref = db.collection('conversations').document(uid).collection('messages').add(data)
        return doc_ref[1].id

    @staticmethod
    def get_conversation_history(uid, limit=50):
        if not db:
            return []
        query = db.collection('conversations').document(uid).collection('messages')
        if gcfirestore:
            query = query.order_by('timestamp', direction=gcfirestore.Query.DESCENDING)
        docs = query.limit(limit).stream()
        return [d.to_dict() for d in docs]

    # MOODS
    @staticmethod
    def save_mood(uid, mood_data):
        if not db:
            return None
        mood_data['user_id'] = uid
        mood_data['timestamp'] = datetime.utcnow()
        doc_ref = db.collection('moods').add(mood_data)
        return doc_ref[1].id

    @staticmethod
    def get_mood_history(uid, days=30):
        if not db:
            return []
        start_date = datetime.utcnow() - timedelta(days=days)
        query = db.collection('moods').where('user_id', '==', uid).where('timestamp', '>=', start_date)
        docs = query.order_by('timestamp').stream() if gcfirestore else query.stream()
        return [d.to_dict() for d in docs]

    # HABITS
    @staticmethod
    def create_habit(uid, habit_data):
        if not db:
            return None
        habit_data['user_id'] = uid
        habit_data['created_at'] = datetime.utcnow()
        habit_data['is_active'] = True
        habit_data['streak'] = 0
        doc_ref = db.collection('habits').add(habit_data)
        return doc_ref[1].id

    @staticmethod
    def log_habit_entry(habit_id, uid, completed):
        if not db:
            return False
        entry = {
            'habit_id': habit_id,
            'user_id': uid,
            'completed': completed,
            'date': datetime.utcnow().date().isoformat(),
            'timestamp': datetime.utcnow()
        }
        db.collection('habit_entries').add(entry)
        if completed:
            ref = db.collection('habits').document(habit_id)
            snap = ref.get()
            if snap.exists:
                current = snap.to_dict().get('streak', 0)
                ref.update({'streak': current + 1})
        return True

    # FILES
    @staticmethod
    def upload_file(file, uid, file_type='general'):
        if not bucket:
            raise RuntimeError('Firebase storage bucket not configured')
        fname = f"{uid}/{file_type}/{uuid.uuid4()}_{file.filename}"
        blob = bucket.blob(fname)
        blob.upload_from_file(file)
        try:
            blob.make_public()
            url = blob.public_url
        except Exception:
            url = blob.path
        return {'url': url, 'path': fname}

    # ANALYTICS (simplified)
    @staticmethod
    def get_user_analytics(uid, period='month'):
        days = 7 if period == 'week' else 30 if period == 'month' else 365
        start_date = datetime.utcnow() - timedelta(days=days)
        moods = []
        habits = []
        if db:
            moods = [m.to_dict() for m in db.collection('moods').where('user_id', '==', uid).where('timestamp', '>=', start_date).stream()]
            habits = [h.to_dict() for h in db.collection('habits').where('user_id', '==', uid).where('is_active', '==', True).stream()]
        return {
            'moods': moods,
            'habits': habits,
            'period': period
        }


