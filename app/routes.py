import os
import requests
from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User
from flask_wtf.csrf import generate_csrf
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import send_from_directory


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
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
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
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Facebook login successful',
        'access_token': access_token
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = User.query.get_or_404(get_jwt_identity())

    profile_url = f"{request.host_url}uploads/profile_pictures/{user.profile_picture}" if user.profile_picture else None

    return jsonify({
        'id': user.id,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'email': user.email,
        'phone': user.phone,
        'profile_picture': profile_url
    }), 200


@auth_bp.route('/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    user = User.query.get_or_404(get_jwt_identity())
    data = request.json or {}

    user.firstname = data.get('firstname', user.firstname)
    user.lastname = data.get('lastname', user.lastname)
    user.phone = data.get('phone', user.phone)

    if data.get('password'):
        user.set_password(data['password'])

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/profile_pictures')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/profile/upload', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    user = User.query.get_or_404(get_jwt_identity())

    file = request.files.get('file')
    if not file or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file type'}), 400

    filename = secure_filename(f"user_{user.id}_{file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)  
    file.save(file_path)

    user.profile_picture = filename  
    db.session.commit()

    profile_url = f"{request.host_url}uploads/profile_pictures/{filename}"  

    return jsonify({'message': 'Profile picture updated', 'profile_picture': profile_url}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/profile/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    user = User.query.get_or_404(get_jwt_identity())

   
    if user.profile_picture:
        file_path = os.path.join(UPLOAD_FOLDER, user.profile_picture)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'Account deleted successfully'}), 200

@auth_bp.route('/api/artist-image')
def get_artist_image():
    artist_name = request.args.get("artist")
    if not artist_name:
        return jsonify({"error": "Missing artist parameter"}), 400

    deezer_url = f"https://api.deezer.com/search/artist?q={artist_name}"
    response = requests.get(deezer_url)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch artist"}), response.status_code

    data = response.json()
    if "data" in data and len(data["data"]) > 0:
        return jsonify({"image": data["data"][0].get("picture_medium", "")})

    return jsonify({"image": "/images/default-artist.jpg"})  # Fallback image

@auth_bp.route('/uploads/profile_pictures/<filename>')
def serve_profile_picture(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)