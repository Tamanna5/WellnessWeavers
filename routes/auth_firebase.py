from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.firebase_service import FirebaseService

auth_bp = Blueprint('auth_api', __name__)
firebase = FirebaseService()

@auth_bp.route('/signup', methods=['POST'])
@cross_origin()
def signup():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    display_name = data.get('display_name')
    result = firebase.create_user(email, password, display_name)
    return jsonify(result)

@auth_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    return jsonify({'message': 'Use Firebase Auth on frontend'})

@auth_bp.route('/user/<uid>', methods=['GET'])
@cross_origin()
def get_user(uid):
    data = firebase.get_user(uid)
    return jsonify(data or {})

@auth_bp.route('/user/<uid>', methods=['PUT'])
@cross_origin()
def update_user(uid):
    data = request.get_json() or {}
    firebase.update_user(uid, data)
    return jsonify({'success': True})


