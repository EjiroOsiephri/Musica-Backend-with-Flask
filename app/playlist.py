from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Playlist, User

playlist_bp = Blueprint('playlist', __name__)

@playlist_bp.route('/add-to-playlist', methods=['POST'])
@jwt_required()
def add_to_playlist():
    user_id = get_jwt_identity()
    data = request.json

    # Validate data
    if not all(key in data for key in ['track_id', 'title', 'artist', 'image', 'preview']):
        return jsonify({'message': 'Missing required fields'}), 400

    # Create a new playlist entry
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
