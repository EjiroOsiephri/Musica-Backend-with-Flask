from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Playlist, User
import requests

playlist_bp = Blueprint('playlist', __name__)

# ✅ Function to verify Google Token
def verify_google_token(token):
    response = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}")
    if response.status_code == 200:
        return response.json()  # Returns user data if token is valid
    return None

# ✅ Function to verify Facebook Token
def verify_facebook_token(token):
    response = requests.get(f"https://graph.facebook.com/me?access_token={token}&fields=id,email")
    if response.status_code == 200:
        return response.json()  # Returns user data if token is valid
    return None

# ✅ Route to add song to playlist
@playlist_bp.route('/add-to-playlist', methods=['POST'])
@jwt_required(optional=True)
def add_to_playlist():
    user_id = get_jwt_identity()  # ✅ Get user ID from JWT if available
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Try social authentication if JWT is missing or invalid
        google_data = verify_google_token(token)
        facebook_data = verify_facebook_token(token)

        if google_data:
            user = User.query.filter_by(email=google_data['email']).first()
            if user:
                user_id = user.id
        elif facebook_data:
            user = User.query.filter_by(email=facebook_data['email']).first()
            if user:
                user_id = user.id

    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.json
    if not all(key in data for key in ['track_id', 'title', 'artist', 'image', 'preview']):
        return jsonify({'message': 'Missing required fields'}), 400

    new_song = Playlist(
        user_id=user_id,
        track_id=data['track_id'],
        title=data['title'],
        artist=data['artist'],
        image=data.get('image', ''),
        preview=data.get('preview', '')
    )

    db.session.add(new_song)
    db.session.commit()

    return jsonify({'message': 'Song added to playlist successfully'}), 201

# ✅ Route to get user playlist
@playlist_bp.route('/get-playlist', methods=['GET'])
@jwt_required(optional=True)
def get_playlist():
    user_id = get_jwt_identity()  # ✅ Get user ID from JWT if available
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Try social authentication if JWT is missing or invalid
        google_data = verify_google_token(token)
        facebook_data = verify_facebook_token(token)

        if google_data:
            user = User.query.filter_by(email=google_data['email']).first()
            if user:
                user_id = user.id
        elif facebook_data:
            user = User.query.filter_by(email=facebook_data['email']).first()
            if user:
                user_id = user.id

    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    playlist_songs = Playlist.query.filter_by(user_id=user_id).all()
    songs_list = [
        {
            'track_id': song.track_id,
            'title': song.title,
            'artist': song.artist,
            'image': song.image,
            'preview': song.preview
        }
        for song in playlist_songs
    ]

    return jsonify({'playlist': songs_list}), 200
