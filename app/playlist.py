from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app import db
from app.models import Playlist, User
import requests

playlist_bp = Blueprint('playlist', __name__)

# Function to verify Google Token
def verify_google_token(token):
    response = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}")
    if response.status_code == 200:
        return response.json()
    return None

# Function to verify Facebook Token
def verify_facebook_token(token):
    response = requests.get(f"https://graph.facebook.com/me?access_token={token}&fields=id,email")
    if response.status_code == 200:
        return response.json()
    return None

# Route to add song to playlist
@playlist_bp.route('/add-to-playlist', methods=['POST'])
@jwt_required(optional=True)
def add_to_playlist():
    user_id = get_jwt_identity()
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Try social authentication if JWT is missing or invalid
        google_data = verify_google_token(token)
        facebook_data = verify_facebook_token(token)

        if google_data:
            user = User.query.filter_by(email=google_data['email']).first()
            if user:
                # Generate JWT for Google user
                access_token = create_access_token(identity=str(user.id))
                return jsonify({
                    'message': 'Google login successful',
                    'access_token': access_token
                }), 200
        elif facebook_data:
            user = User.query.filter_by(email=facebook_data['email']).first()
            if user:
                # Generate JWT for Facebook user
                access_token = create_access_token(identity=str(user.id))
                return jsonify({
                    'message': 'Facebook login successful',
                    'access_token': access_token
                }), 200

    # If JWT is present or was generated above, proceed with the request
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # If we reach here, user_id should be valid
    data = request.json
    if not all(key in data for key in ['track_id', 'title', 'artist', 'image', 'preview']):
        return jsonify({'message': 'Missing required fields'}), 400

    new_song = Playlist(
        user_id=user_id,
        track_id=data['track_id'],
        title=data['title'],
        artist=data['artist'],
        image=data.get('image', ''),
        preview=data.get('preview', ''),
        album=data.get('album', ''), 
        duration=data.get('duration', '')  
    )

    db.session.add(new_song)
    db.session.commit()

    return jsonify({'message': 'Song added to playlist successfully'}), 201

# Route to get user playlist
@playlist_bp.route('/get-playlist', methods=['GET'])
@jwt_required(optional=True)
def get_playlist():
    user_id = get_jwt_identity()
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Try social authentication if JWT is missing or invalid
        google_data = verify_google_token(token)
        facebook_data = verify_facebook_token(token)

        if google_data:
            user = User.query.filter_by(email=google_data['email']).first()
            if user:
                # Generate JWT for Google user
                access_token = create_access_token(identity=str(user.id))
                return jsonify({
                    'message': 'Google login successful',
                    'access_token': access_token
                }), 200
        elif facebook_data:
            user = User.query.filter_by(email=facebook_data['email']).first()
            if user:
                # Generate JWT for Facebook user
                access_token = create_access_token(identity=str(user.id))
                return jsonify({
                    'message': 'Facebook login successful',
                    'access_token': access_token
                }), 200

    # If JWT is present or was generated above, proceed with the request
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    playlist_songs = Playlist.query.filter_by(user_id=user_id).all()
    songs_list = [
        {
            'track_id': song.track_id,
            'title': song.title,
            'artist': song.artist,
            'image': song.image,
            'preview': song.preview,
            'album': song.album,
            'duration': song.duration

        }
        for song in playlist_songs
    ]

    return jsonify({'playlist': songs_list}), 200


@playlist_bp.route('/delete-from-playlist/<int:track_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_from_playlist(track_id):
    user_id = get_jwt_identity()
    auth_header = request.headers.get("Authorization")

    if not user_id and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

       
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

    song = Playlist.query.filter_by(user_id=user_id, track_id=track_id).first()

    if not song:
        return jsonify({'message': 'Song not found in playlist'}), 404

    db.session.delete(song)
    db.session.commit()

    return jsonify({'message': 'Song deleted from playlist successfully'}), 200
