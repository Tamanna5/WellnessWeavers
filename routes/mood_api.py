from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.firebase_service import FirebaseService

mood_bp = Blueprint('mood_api', __name__)
firebase = FirebaseService()

@mood_bp.route('/', methods=['POST'])
@cross_origin()
def log_mood():
    data = request.get_json() or {}
    uid = data.get('uid')
    mood_id = firebase.save_mood(uid, {
        'mood_score': data.get('mood_score'),
        'emotion': data.get('emotion'),
        'emotions': data.get('emotions', []),
        'intensity': data.get('intensity'),
        'notes': data.get('notes'),
        'activities': data.get('activities', []),
        'triggers': data.get('triggers', []),
        'location': data.get('location'),
        'weather': data.get('weather')
    })
    user = firebase.get_user(uid) or {}
    points = user.get('total_points', 0) + 10
    firebase.update_user(uid, {'total_points': points})
    return jsonify({'success': True, 'mood_id': mood_id, 'points_earned': 10})

@mood_bp.route('/history/<uid>', methods=['GET'])
@cross_origin()
def get_mood_history(uid):
    days = request.args.get('days', 30, type=int)
    moods = firebase.get_mood_history(uid, days)
    return jsonify({'moods': moods})


