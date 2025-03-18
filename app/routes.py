from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token
import requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    # Create new user
    new_user = User(
        firstname=data['firstname'],
        lastname=data['lastname'],
        phone=data.get('phone', '0000000000'),  # Default phone number if missing
        email=data['email']
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    # Generate JWT Token
    access_token = create_access_token(identity=str(new_user.id))

    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': new_user.id,
            'firstname': new_user.firstname,
            'lastname': new_user.lastname,
            'phone': new_user.phone,
            'email': new_user.email
        },
        'access_token': access_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'phone': user.phone,
            'email': user.email
        },
        'access_token': access_token
    }), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    token = request.json.get("token")
    response = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}")
    user_info = response.json()

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            firstname=user_info.get('given_name', 'Unknown'),
            lastname=user_info.get('family_name', 'User'),
            email=user_info['email'],
            phone='0000000000',  # Dummy phone number for OAuth users
            google_id=user_info.get('sub', '')  # Ensure google_id is set
        )
        db.session.add(user)
        db.session.commit()

    if not user.id:
        return jsonify({"error": "User ID missing"}), 500  # Ensure user ID is valid

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'Google login successful',
        'access_token': access_token
    })

@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    token = request.json.get("token")
    response = requests.get(f"https://graph.facebook.com/me?access_token={token}&fields=id,name,email")
    user_info = response.json()

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        name_parts = user_info['name'].split()
        user = User(
            firstname=name_parts[0],
            lastname=name_parts[1] if len(name_parts) > 1 else "User",
            email=user_info['email'],
            phone='0000000000',  # Dummy phone number for OAuth users
            facebook_id=user_info.get('id', '')  # Ensure facebook_id is set
        )
        db.session.add(user)
        db.session.commit()

    if not user.id:
        return jsonify({"error": "User ID missing"}), 500  # Ensure user ID is valid

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'Facebook login successful',
        'access_token': access_token
    })
