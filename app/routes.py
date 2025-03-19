from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token
from flask_wtf.csrf import generate_csrf
import requests

auth_bp = Blueprint('auth', __name__)


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



@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    token = request.json.get("token")

    # Validate Facebook token and fetch user info
    response = requests.get(f"https://graph.facebook.com/me?access_token={token}&fields=id,first_name,last_name,email")
    user_info = response.json()

    if 'email' not in user_info:
        return jsonify({'error': 'Invalid Facebook token'}), 401

    # Check if user exists in the database
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
    access_token = create_access_token(identity=str(user.id))  # 🔥 Now it matches normal login

    return jsonify({
        'message': 'Facebook login successful',
        'access_token': access_token
    })



def validate_google_token(token):
    """Validate Google OAuth token and return user info"""
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

    access_token = create_access_token(identity=str(user.id))

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