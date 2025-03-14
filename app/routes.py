from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token
import requests
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(
        firstname=data['firstname'],
        lastname=data['lastname'],
        phone=data['phone'],
        email=data['email']
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    token = request.json.get("token")
    response = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}")
    user_info = response.json()

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(first_name=user_info['given_name'], last_name=user_info['family_name'], email=user_info['email'], google_id=user_info['sub'])
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token})

@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    token = request.json.get("token")
    response = requests.get(f"https://graph.facebook.com/me?access_token={token}&fields=id,name,email")
    user_info = response.json()

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(first_name=user_info['name'].split()[0], last_name=user_info['name'].split()[1], email=user_info['email'], facebook_id=user_info['id'])
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token})
