import os
import requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token
from flask_wtf.csrf import generate_csrf
from datetime import timedelta



auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(
        firstname=data.get('firstname', 'Unknown'),
        lastname=data.get('lastname', 'User'),
        phone=data.get('phone', '0000000000'),
        email=email
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id),expires_delta=timedelta(days=7))

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
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id),expires_delta=timedelta(days=7))

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

def validate_google_token(token):
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    google_token = request.json.get("token")
    user_info = validate_google_token(google_token)
    
    if not user_info or 'email' not in user_info:
        return jsonify({'error': 'Invalid Google token'}), 401

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            firstname=user_info.get('given_name', 'Unknown'),
            lastname=user_info.get('family_name', 'User'),
            email=user_info['email'],
            phone='0000000000',
            google_id=user_info.get('sub', '')
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=str(user.id),expires_delta=timedelta(days=7))

    return jsonify({
        'message': 'Google login successful',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'firstname': user.firstname,
            'lastname': user.lastname
        }
    }), 200

def exchange_facebook_code_for_token(code):
    """Exchange Facebook OAuth code for an access token."""
    try:
        response = requests.get(
            "https://graph.facebook.com/v12.0/oauth/access_token",
            params={
                "client_id": os.environ.get("FACEBOOK_CLIENT_ID"),
                "client_secret": os.environ.get("FACEBOOK_CLIENT_SECRET"),
                "redirect_uri": os.environ.get("FACEBOOK_REDIRECT_URI"),
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException as e:
        print(f"Error exchanging Facebook code for token: {e}")
        return None

@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    code = request.json.get("token")

    # Exchange the code for an access token
    access_token = exchange_facebook_code_for_token(code)
    if not access_token:
        return jsonify({'error': 'Failed to exchange Facebook code for token'}), 401

    # Fetch user info using the access token
    response = requests.get(
        "https://graph.facebook.com/me",
        params={
            "access_token": access_token,
            "fields": "id,first_name,last_name,email",
        },
    )
    user_info = response.json()

    if 'email' not in user_info:
        return jsonify({'error': 'Invalid Facebook token'}), 401

    # Find or create user
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            firstname=user_info.get('first_name', 'Unknown'),
            lastname=user_info.get('last_name', 'User'),
            email=user_info['email'],
            phone='0000000000',  # Dummy phone number for OAuth users
            facebook_id=user_info.get('id', '')  # Store Facebook ID
        )
        db.session.add(user)
        db.session.commit()

    if not user.id:
        return jsonify({"error": "User ID missing"}), 500  # Ensure user ID is valid

    # Generate JWT access token for the user
    access_token = create_access_token(identity=str(user.id),expires_delta=timedelta(days=7))

    return jsonify({
        'message': 'Facebook login successful',
        'access_token': access_token
    })