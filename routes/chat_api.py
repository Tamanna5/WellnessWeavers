from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.firebase_service import FirebaseService

chat_bp = Blueprint('chat_api', __name__)
firebase = FirebaseService()

@chat_bp.route('/message', methods=['POST'])
@cross_origin()
def send_message():
    data = request.get_json() or {}
    message = data.get('message', '')
    uid = data.get('uid')
    persona = data.get('persona', 'Priya')
    # Placeholder response until AI pipeline connected
    response_text = f"[{persona}] I hear you. Tell me more about that."
    firebase.save_conversation(uid, message, response_text, metadata={})
    return jsonify({'message': response_text, 'persona': persona})

@chat_bp.route('/history/<uid>', methods=['GET'])
@cross_origin()
def get_history(uid):
    limit = request.args.get('limit', 50, type=int)
    history = firebase.get_conversation_history(uid, limit)
    return jsonify({'history': history})


